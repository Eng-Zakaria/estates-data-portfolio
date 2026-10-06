"""Reconcile IFC model vs space register: area delta per room, rooms in model not in register and vice versa.

Output: recon_model_vs_register table + summary by building.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

TRUTH = Path("data/truth")


def reconcile(tables: dict[str, pd.DataFrame], out_dir: Path) -> pd.DataFrame:
    out_dir.mkdir(parents=True, exist_ok=True)

    spaces_ifc = tables.get("ifc_spaces", pd.DataFrame())
    truth_spaces = pd.read_parquet(TRUTH / "spaces.parquet")

    # Join on room_code = space name
    ifc_rooms = spaces_ifc.rename(columns={"name": "room_code"})[["room_code", "area_m2"]].copy()
    ifc_rooms["area_m2"] = pd.to_numeric(ifc_rooms["area_m2"], errors="coerce")

    merged = truth_spaces.merge(ifc_rooms, on="room_code", how="outer", indicator=True)
    merged["area_delta"] = merged["area_m2"] - merged["nia_m2"]
    merged["area_delta_pct"] = (merged["area_delta"] / merged["nia_m2"] * 100).round(2)
    merged["status"] = merged["_merge"].map(
        {
            "both": "matched",
            "left_only": "missing_from_model",
            "right_only": "missing_from_register",
        }
    )

    recon = merged[["room_code", "building_id", "nia_m2", "area_m2", "area_delta", "area_delta_pct", "status"]].copy()
    recon.to_parquet(out_dir / "recon_model_vs_register.parquet", index=False)

    # Summary by building
    summary = recon.groupby(["building_id", "status"]).size().unstack(fill_value=0).reset_index()
    summary.to_csv(out_dir / "recon_summary_by_building.csv", index=False)

    # Planted defect recall
    mismatch = recon[(recon["status"] == "matched") & (recon["area_delta_pct"].abs() > 10)]
    missing = recon[recon["status"] == "missing_from_model"]
    print(f"Reconciliation: {len(recon)} rooms")
    print(f"  Matched: {len(recon[recon['status'] == 'matched'])}")
    print(f"  Missing from model: {len(missing)}")
    print(f"  Missing from register: {len(recon[recon['status'] == 'missing_from_register'])}")
    print(f"  Area mismatch >10%: {len(mismatch)}")
    return recon


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--tables", type=Path, default=Path("data/gold/ifc"))
    parser.add_argument("--out", type=Path, default=Path("data/gold/ifc"))
    args = parser.parse_args()
    tables = {p.stem: pd.read_parquet(p) for p in args.tables.glob("*.parquet")}
    reconcile(tables, args.out)
