"""COBie rules engine: load YAML rules, validate workbook, produce issue list.

Each issue: sheet, row, column, rule_id, severity (blocking/warning), message, suggested_fix.

Score: weighted completeness, 100 - 1.5*blocking - 0.5*warning, floored at 0.
Blocking = structural/keys/FK failures (CI gate); warning = format/AIR issues.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

MULTI_SPLIT = re.compile(r"[,;|]")


@dataclass
class Issue:
    sheet: str
    row: int | None
    column: str | None
    rule_id: str
    severity: str  # blocking or warning
    message: str
    suggested_fix: str = ""


@dataclass
class ValidationResult:
    issues: list[Issue] = field(default_factory=list)
    score: float = 100.0

    @property
    def blocking_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "blocking")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")

    def has_blocking(self) -> bool:
        return self.blocking_count > 0

    def per_sheet(self) -> pd.DataFrame:
        if not self.issues:
            return pd.DataFrame(columns=["sheet", "blocking", "warning"])
        df = issues_to_df(self.issues)
        out = (
            df.groupby("sheet")
            .agg(
                blocking=("severity", lambda s: int((s == "blocking").sum())),
                warning=("severity", lambda s: int((s == "warning").sum())),
            )
            .reset_index()
        )
        return out.sort_values("sheet")


def _split_multi(cell: object) -> list[str]:
    return [p.strip() for p in MULTI_SPLIT.split(str(cell)) if p.strip()]


def validate_workbook(path: Path, cobie_rules: list[dict], air_rules: list[dict]) -> ValidationResult:
    result = ValidationResult()
    try:
        dfs = pd.read_excel(path, sheet_name=None)
    except Exception as e:
        result.issues.append(Issue("workbook", None, None, "read_error", "blocking", str(e)))
        result.score = 0.0
        return result

    for rule in cobie_rules:
        rtype = rule.get("type")
        rid = rule.get("id", rtype or "rule")
        sev = rule.get("severity", "blocking")

        if rtype == "sheet_present":
            sheet = rule["sheet"]
            if sheet not in dfs:
                result.issues.append(
                    Issue(
                        sheet,
                        None,
                        None,
                        rid,
                        "blocking",
                        f"Missing sheet: {sheet}",
                        f"Add sheet '{sheet}' to the workbook",
                    )
                )

        elif rtype == "column_present":
            sheet, col = rule["sheet"], rule["column"]
            if sheet in dfs and col not in dfs[sheet].columns:
                result.issues.append(
                    Issue(
                        sheet, None, col, rid, sev, f"Missing column: {col}", f"Add column '{col}' to sheet '{sheet}'"
                    )
                )

        elif rtype == "column_order":
            sheet = rule["sheet"]
            expected: list = rule["columns"]
            if sheet in dfs:
                actual = list(dfs[sheet].columns[: len(expected)])
                if actual != expected:
                    result.issues.append(
                        Issue(
                            sheet,
                            None,
                            None,
                            rid,
                            sev,
                            f"Column order mismatch: expected {expected}, got {actual}",
                            "Reorder columns to match the COBie spec order",
                        )
                    )

        elif rtype == "mandatory_not_empty":
            sheet, col = rule["sheet"], rule["column"]
            if sheet in dfs and col in dfs[sheet].columns:
                empty = dfs[sheet][col].isna() | (dfs[sheet][col].astype(str) == "")
                for idx in dfs[sheet][empty].index:
                    result.issues.append(
                        Issue(
                            sheet, int(idx) + 2, col, rid, "blocking", "Empty mandatory cell", f"Fill in {sheet}.{col}"
                        )
                    )

        elif rtype == "unique_key":
            sheet, col = rule["sheet"], rule["column"]
            if sheet in dfs and col in dfs[sheet].columns:
                series = dfs[sheet][col]
                mask = series.notna() & (series.astype(str) != "")
                dups = dfs[sheet][mask & series.duplicated(keep=False)]
                for idx in dups.index:
                    result.issues.append(
                        Issue(
                            sheet,
                            int(idx) + 2,
                            col,
                            rid,
                            "blocking",
                            f"Duplicate key: {series.loc[idx]}",
                            "Make this key unique",
                        )
                    )

        elif rtype == "fk":
            src_sheet, src_col = rule["src_sheet"], rule["src_column"]
            dst_sheet, dst_col = rule["dst_sheet"], rule["dst_column"]
            multi = rule.get("multi_value", False)
            if (
                src_sheet in dfs
                and dst_sheet in dfs
                and src_col in dfs[src_sheet].columns
                and dst_col in dfs[dst_sheet].columns
            ):
                dst_values = set(dfs[dst_sheet][dst_col].dropna().astype(str))
                for idx, val in dfs[src_sheet][src_col].items():
                    if pd.isna(val) or str(val) == "":
                        continue
                    tokens = _split_multi(val) if multi else [str(val).strip()]
                    for tok in tokens:
                        if tok not in dst_values:
                            result.issues.append(
                                Issue(
                                    src_sheet,
                                    int(idx) + 2,
                                    src_col,
                                    rid,
                                    "blocking",
                                    f"FK not found in {dst_sheet}.{dst_col}: {tok}",
                                    f"Point {src_sheet}.{src_col} at an existing {dst_sheet}.{dst_col}",
                                )
                            )

        elif rtype == "created_by":
            contact_sheet = rule.get("contact_sheet", "Contact")
            contact_col = rule.get("contact_column", "Email")
            contacts: set[str] = set()
            if contact_sheet in dfs and contact_col in dfs[contact_sheet].columns:
                contacts = set(dfs[contact_sheet][contact_col].dropna().astype(str))
            for sheet, df in dfs.items():
                if "CreatedBy" in df.columns:
                    for idx, val in df["CreatedBy"].items():
                        if pd.notna(val) and str(val) != "" and str(val) not in contacts:
                            result.issues.append(
                                Issue(
                                    sheet,
                                    int(idx) + 2,
                                    "CreatedBy",
                                    rid,
                                    "blocking",
                                    f"CreatedBy not in Contact: {val}",
                                    "Use a Contact.Email address for CreatedBy",
                                )
                            )

        elif rtype == "format":
            sheet, col, pattern = rule["sheet"], rule["column"], rule.get("pattern")
            fix = rule.get("fix", f"Match pattern {pattern}")
            if sheet in dfs and col in dfs[sheet].columns and pattern:
                rx = re.compile(pattern)
                for idx, val in dfs[sheet][col].items():
                    if pd.notna(val) and str(val) != "" and not rx.match(str(val)):
                        result.issues.append(Issue(sheet, int(idx) + 2, col, rid, sev, f"Format mismatch: {val}", fix))

        elif rtype == "numeric_range":
            sheet, col = rule["sheet"], rule["column"]
            lo, hi = rule.get("min"), rule.get("max")
            if sheet in dfs and col in dfs[sheet].columns:
                for idx, val in dfs[sheet][col].items():
                    if pd.isna(val) or str(val) == "":
                        continue
                    try:
                        num = float(val)
                    except (TypeError, ValueError):
                        result.issues.append(
                            Issue(
                                sheet, int(idx) + 2, col, rid, "warning", f"Non-numeric value: {val}", "Enter a number"
                            )
                        )
                        continue
                    if (lo is not None and num < lo) or (hi is not None and num > hi):
                        result.issues.append(
                            Issue(
                                sheet,
                                int(idx) + 2,
                                col,
                                rid,
                                "warning",
                                f"Out of range [{lo}, {hi}]: {val}",
                                f"Enter a value between {lo} and {hi}",
                            )
                        )

        elif rtype == "category_pattern":
            sheet, col, pattern = rule["sheet"], rule["column"], rule.get("pattern")
            if sheet in dfs and col in dfs[sheet].columns and pattern:
                rx = re.compile(pattern)
                for idx, val in dfs[sheet][col].items():
                    if pd.notna(val) and str(val) != "" and not rx.match(str(val)):
                        result.issues.append(
                            Issue(
                                sheet,
                                int(idx) + 2,
                                col,
                                rid,
                                rule.get("severity", "warning"),
                                f"Invalid category: {val}",
                                "Use a plain asset category label",
                            )
                        )

    for rule in air_rules:
        if rule.get("type") == "required_attribute":
            sheet, col = rule["sheet"], rule["column"]
            if sheet in dfs and col in dfs[sheet].columns:
                missing = dfs[sheet][col].isna() | (dfs[sheet][col].astype(str) == "")
                for idx in dfs[sheet][missing].index:
                    result.issues.append(
                        Issue(
                            sheet,
                            int(idx) + 2,
                            col,
                            rule["id"],
                            "warning",
                            f"Missing AIR attribute: {col}",
                            f"Provide {col} per the AIR",
                        )
                    )

    result.score = max(0.0, round(100.0 - 1.5 * result.blocking_count - 0.5 * result.warning_count, 1))
    return result


def issues_to_df(issues: list[Issue]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "sheet": i.sheet,
                "row": i.row,
                "column": i.column,
                "rule_id": i.rule_id,
                "severity": i.severity,
                "message": i.message,
                "suggested_fix": i.suggested_fix,
            }
            for i in issues
        ]
    )
