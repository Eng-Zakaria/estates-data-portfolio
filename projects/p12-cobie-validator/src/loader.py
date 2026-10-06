"""Handover loader: map COBie Type/Component/Space into a staging asset register.

Matching order per Component row:
  1. serial match against the existing truth asset register (if provided), else
  2. workbook-internal duplicate serial -> rejected (quarantine),
  3. space+type fallback is recorded in staging for later matching.

Outcome per row: inserted / updated / unchanged / rejected.
Idempotent re-run: a state.json of row hashes is kept in the output dir; a
second run with the same workbook reports all rows as unchanged.
--dry-run computes the diff report without writing staging/quarantine/state.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

# COBie Category -> internal asset_type (foundation truth uses these labels).
CATEGORY_MAP = {
    "Boiler": "Boiler",
    "Air Handling Unit": "AHU",
    "Fan Coil": "Fan Coil",
    "Pump": "Pump",
    "Lighting": "Lighting",
}


def _row_hash(row: pd.Series) -> str:
    blob = "|".join("" if pd.isna(v) else str(v) for v in row.values)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def load_workbook_to_staging(
    workbook: Path,
    out_dir: Path,
    truth_assets: Path | None = None,
    dry_run: bool = False,
) -> dict:
    dfs = pd.read_excel(workbook, sheet_name=None)
    comp = dfs.get("Component", pd.DataFrame()).copy()
    typ = dfs.get("Type", pd.DataFrame()).copy()
    space = dfs.get("Space", pd.DataFrame()).copy()

    type_names = set(typ["Name"].dropna().astype(str)) if "Name" in typ.columns else set()
    space_names = set(space["Name"].dropna().astype(str)) if "Name" in space.columns else set()

    truth_serials: dict[str, dict] = {}
    if truth_assets is not None and truth_assets.exists():
        t = pd.read_parquet(truth_assets)
        if "serial_no" in t.columns:
            for _, r in t.iterrows():
                truth_serials[str(r["serial_no"])] = r.to_dict()

    staged_rows: list[dict] = []
    quarantine_rows: list[dict] = []
    seen_serials: dict[str, int] = {}

    for idx, row in comp.iterrows():
        excel_row = int(idx) + 2
        name = "" if pd.isna(row.get("Name")) else str(row.get("Name"))
        type_name = "" if pd.isna(row.get("TypeName")) else str(row.get("TypeName"))
        space_name = "" if pd.isna(row.get("Space")) else str(row.get("Space"))
        serial = "" if pd.isna(row.get("SerialNumber")) else str(row.get("SerialNumber"))
        install = "" if pd.isna(row.get("InstallationDate")) else str(row.get("InstallationDate"))
        category = "" if pd.isna(row.get("Category")) else str(row.get("Category"))

        reasons: list[str] = []
        if not type_name:
            reasons.append("missing TypeName")
        elif type_name not in type_names:
            reasons.append(f"unknown TypeName {type_name}")
        # multi-value Space cells: accept if at least one token resolves
        tokens = [p.strip() for p in str(space_name).replace(";", ",").split(",") if p.strip()]
        if not space_name:
            reasons.append("missing Space")
        elif space_names and not any(t in space_names for t in tokens):
            reasons.append(f"unknown Space {space_name}")
        if not serial:
            reasons.append("missing SerialNumber")
        elif serial in seen_serials:
            reasons.append(f"duplicate SerialNumber {serial} (also row {seen_serials[serial]})")
        else:
            seen_serials.setdefault(serial, excel_row)

        if reasons:
            quarantine_rows.append({"row": excel_row, "Name": name, "reasons": "; ".join(reasons)})
            continue

        asset_type = CATEGORY_MAP.get(category, category or "Unknown")
        first_space = [p.strip() for p in re.split(r"[,;|]", space_name) if p.strip()]
        staged_rows.append(
            {
                "component_name": name,
                "type_name": type_name,
                "space": first_space[0] if first_space else "",
                "serial": serial,
                "install_date": install,
                "asset_type": asset_type,
                "truth_match": "serial" if serial in truth_serials else "space+type",
            }
        )

    state_path = out_dir / "state.json"
    prev_hashes: dict[str, str] = {}
    if state_path.exists():
        prev_hashes = json.loads(state_path.read_text(encoding="utf-8"))

    counts = {"inserted": 0, "updated": 0, "unchanged": 0, "rejected": len(quarantine_rows)}
    current_hashes: dict[str, str] = {}
    for r in staged_rows:
        key = r["serial"] or r["component_name"]
        h = hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()[:16]
        current_hashes[key] = h
        if key not in prev_hashes:
            counts["inserted"] += 1
        elif prev_hashes[key] == h:
            counts["unchanged"] += 1
        else:
            counts["updated"] += 1

    wb_bytes = workbook.read_bytes()
    audit = {
        "workbook": workbook.name,
        "workbook_sha256": hashlib.sha256(wb_bytes).hexdigest(),
        "run_utc": datetime.now(UTC).isoformat(),
        "counts": counts,
        "dry_run": dry_run,
    }

    diff_lines = [f"# Handover diff for {workbook.name}", ""]
    diff_lines.append(
        f"inserted={counts['inserted']} updated={counts['updated']} "
        f"unchanged={counts['unchanged']} rejected={counts['rejected']}"
    )
    for r in staged_rows:
        key = r["serial"] or r["component_name"]
        status = "new" if key not in prev_hashes else ("same" if prev_hashes[key] == current_hashes[key] else "changed")
        diff_lines.append(
            f"- [{status}] {r['component_name']} serial={r['serial']} "
            f"space={r['space']} type={r['type_name']} -> {r['asset_type']}"
        )
    for q in quarantine_rows:
        diff_lines.append(f"- [REJECT row {q['row']}] {q['Name']}: {q['reasons']}")
    diff_md = "\n".join(diff_lines) + "\n"

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(staged_rows).to_csv(out_dir / "staging_components.csv", index=False)
        pd.DataFrame(quarantine_rows).to_csv(out_dir / "quarantine.csv", index=False)
        (out_dir / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
        state_path.write_text(json.dumps(current_hashes, indent=2), encoding="utf-8")
        (out_dir / "diff.md").write_text(diff_md, encoding="utf-8")

    return {"counts": counts, "audit": audit, "diff": diff_md, "staged": staged_rows, "quarantine": quarantine_rows}
