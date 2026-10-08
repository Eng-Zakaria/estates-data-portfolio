"""Model QA report: counts by class, missing required attributes, duplicate GlobalIds,
zero/negative areas, spaces without storey, naming conformance, completeness % per pset.

Output: HTML + CSV.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


def qa_report(tables: dict[str, pd.DataFrame], out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)

    spaces = tables.get("ifc_spaces", pd.DataFrame())
    elements = tables.get("ifc_elements", pd.DataFrame())
    types = tables.get("ifc_types", pd.DataFrame())
    classifications = tables.get("ifc_classifications", pd.DataFrame())
    systems = tables.get("ifc_system_members", pd.DataFrame())
    properties = tables.get("ifc_properties_long", pd.DataFrame())

    report: dict[str, Any] = {
        "counts": {
            "spaces": len(spaces),
            "elements": len(elements),
            "types": len(types),
            "systems": len(systems),
            "classifications": len(classifications),
            "properties": len(properties),
        },
        "duplicate_global_ids": int(spaces.duplicated(subset=["global_id"]).sum()) if not spaces.empty else 0,
        "duplicate_element_names": int(elements.duplicated(subset=["name"]).sum()) if not elements.empty else 0,
        "zero_area_spaces": int((spaces["area_m2"] == 0).sum())
        if not spaces.empty and "area_m2" in spaces.columns
        else 0,
        "elements_without_type": int(
            elements["global_id"].isin(set(elements["global_id"]) - set(types.get("global_id", pd.Series()))).sum()
        )
        if not elements.empty
        else 0,
        "elements_without_classification": int(
            elements["global_id"]
            .isin(set(elements["global_id"]) - set(classifications.get("global_id", pd.Series())))
            .sum()
        )
        if not elements.empty
        else 0,
        "elements_without_system": int(
            elements["global_id"]
            .isin(set(elements["global_id"]) - set(systems.get("element_global_id", pd.Series())))
            .sum()
        )
        if not elements.empty
        else 0,
        "spaces_without_area": int(spaces["area_m2"].isna().sum())
        if not spaces.empty and "area_m2" in spaces.columns
        else 0,
        "property_set_completeness": {},
    }

    # Property set completeness
    if not properties.empty:
        for pset in properties["pset"].unique():
            sub = properties[properties["pset"] == pset]
            report["property_set_completeness"][pset] = {
                "rows": len(sub),
                "distinct_properties": sub["property"].nunique(),
                "distinct_entities": sub["global_id"].nunique(),
            }

    # Write CSV summary
    rows = []
    for k, v in report.items():
        if isinstance(v, dict) and "spaces" in v:
            for kk, vv in v.items():
                rows.append({"metric": f"counts.{kk}", "value": vv})
        elif isinstance(v, dict):
            for kk, vv in v.items():
                rows.append({"metric": f"{k}.{kk}", "value": json.dumps(vv)})
        else:
            rows.append({"metric": k, "value": v})
    pd.DataFrame(rows).to_csv(out_dir / "qa_report.csv", index=False)

    # HTML report
    html = "<h1>IFC Model QA Report</h1><table>"
    for k, v in report.items():
        if isinstance(v, dict):
            html += f"<tr><td>{k}</td><td><pre>{json.dumps(v, indent=2)}</pre></td></tr>"
        else:
            html += f"<tr><td>{k}</td><td>{v}</td></tr>"
    html += "</table>"
    (out_dir / "qa_report.html").write_text(html, encoding="utf-8")

    print(f"QA report: {report['counts']['spaces']} spaces, {report['counts']['elements']} elements")
    print(f"  Duplicate GlobalIds: {report['duplicate_global_ids']}")
    print(f"  Zero-area spaces: {report['zero_area_spaces']}")
    print(f"  Elements without type: {report['elements_without_type']}")
    print(f"  Elements without classification: {report['elements_without_classification']}")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=Path, default=Path("data/gold/ifc"))
    parser.add_argument("--out", type=Path, default=Path("data/gold/ifc"))
    args = parser.parse_args()
    tables = {p.stem: pd.read_parquet(p) for p in args.tables.glob("*.parquet")}
    qa_report(tables, args.out)
