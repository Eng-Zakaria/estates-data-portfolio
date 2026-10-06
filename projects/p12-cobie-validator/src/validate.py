"""COBie rules engine: load YAML rules, validate workbook, produce issue list.

Each issue: sheet, row, column, rule_id, severity (blocking/warning), message, suggested_fix.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from spec import load_rules


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


def validate_workbook(path: Path, cobie_rules: list[dict], air_rules: list[dict]) -> ValidationResult:
    result = ValidationResult()
    try:
        dfs = pd.read_excel(path, sheet_name=None)
    except Exception as e:
        result.issues.append(Issue("workbook", None, None, "read_error", "blocking", str(e)))
        return result

    # Structural: sheets present
    expected_sheets = [r.get("sheet") for r in cobie_rules if r.get("type") == "sheet_present"]
    for sheet in expected_sheets:
        if sheet not in dfs:
            result.issues.append(Issue(sheet, None, None, "sheet_present", "blocking", f"Missing sheet: {sheet}"))

    # Structural: columns present
    for rule in cobie_rules:
        if rule.get("type") == "column_present":
            sheet = rule["sheet"]
            col = rule["column"]
            if sheet in dfs and col not in dfs[sheet].columns:
                result.issues.append(
                    Issue(sheet, None, col, rule["id"], rule.get("severity", "blocking"), f"Missing column: {col}")
                )

    # Mandatory fields not empty
    for rule in cobie_rules:
        if rule.get("type") == "mandatory_not_empty":
            sheet = rule["sheet"]
            col = rule["column"]
            if sheet in dfs and col in dfs[sheet].columns:
                empty = dfs[sheet][col].isna() | (dfs[sheet][col] == "")
                for idx in dfs[sheet][empty].index:
                    result.issues.append(Issue(sheet, idx + 2, col, rule["id"], "blocking", f"Empty mandatory cell"))

    # Duplicate keys
    for rule in cobie_rules:
        if rule.get("type") == "unique_key":
            sheet = rule["sheet"]
            col = rule["column"]
            if sheet in dfs and col in dfs[sheet].columns:
                dups = dfs[sheet][dfs[sheet][col].duplicated(keep=False)]
                for idx in dups.index:
                    result.issues.append(
                        Issue(sheet, idx + 2, col, rule["id"], "blocking", f"Duplicate key: {dfs[sheet].loc[idx, col]}")
                    )

    # Foreign keys
    for rule in cobie_rules:
        if rule.get("type") == "fk":
            src_sheet = rule["src_sheet"]
            src_col = rule["src_column"]
            dst_sheet = rule["dst_sheet"]
            dst_col = rule["dst_column"]
            if (
                src_sheet in dfs
                and dst_sheet in dfs
                and src_col in dfs[src_sheet].columns
                and dst_col in dfs[dst_sheet].columns
            ):
                dst_values = set(dfs[dst_sheet][dst_col].dropna().astype(str))
                for idx, val in dfs[src_sheet][src_col].items():
                    if pd.notna(val) and str(val) not in dst_values:
                        result.issues.append(
                            Issue(
                                src_sheet,
                                idx + 2,
                                src_col,
                                rule["id"],
                                "blocking",
                                f"FK not found in {dst_sheet}.{dst_col}: {val}",
                            )
                        )

    # Format rules
    for rule in cobie_rules:
        if rule.get("type") == "format":
            sheet = rule["sheet"]
            col = rule["column"]
            pattern = rule.get("pattern")
            if sheet in dfs and col in dfs[sheet].columns:
                for idx, val in dfs[sheet][col].items():
                    if pd.notna(val) and pattern and not re.match(pattern, str(val)):
                        result.issues.append(
                            Issue(
                                sheet,
                                idx + 2,
                                col,
                                rule["id"],
                                rule.get("severity", "warning"),
                                f"Format mismatch: {val}",
                            )
                        )

    # AIR rules
    for rule in air_rules:
        if rule.get("type") == "required_attribute":
            sheet = rule["sheet"]
            col = rule["column"]
            if sheet in dfs and col in dfs[sheet].columns:
                missing = dfs[sheet][col].isna() | (dfs[sheet][col] == "")
                for idx in dfs[sheet][missing].index:
                    result.issues.append(
                        Issue(sheet, idx + 2, col, rule["id"], "warning", f"Missing AIR attribute: {col}")
                    )

    # Score: weighted completeness
    total_checks = len(cobie_rules) + len(air_rules)
    failed = len(result.issues)
    result.score = max(0.0, 100.0 * (1 - failed / max(total_checks, 1)))

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
