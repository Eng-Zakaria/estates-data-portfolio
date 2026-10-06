"""Build entity_crosswalk: canonical_id ↔ system ↔ native_id (P18).

One row per (canonical_id, system, native_id) covering:
- space register (room_code)
- CAFM (asset_id, space_id)
- IFC (GlobalId for spaces)
- BMS (point_id)
- Meter (meter_id)
- Sensor (sensor_id)
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def build_crosswalk() -> pd.DataFrame:
    """Build the entity crosswalk from gold marts and truth parquet."""
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    rows = []

    # 1. Spaces: canonical space_id from dim_space (prefix space:)
    spaces = con.execute("""
        SELECT space_id, room_code
        FROM main.dim_space
    """).fetchdf()
    for _, r in spaces.iterrows():
        rows.append({
            "canonical_id": f"space:{r['space_id']}",
            "system": "space_register",
            "native_id": r["room_code"],
        })
        # IFC GlobalId from truth spaces parquet
        rows.append({
            "canonical_id": f"space:{r['space_id']}",
            "system": "ifc",
            "native_id": r["space_id"],  # will be enriched below
        })

    # 2. Assets: canonical asset_id from dim_asset (prefix asset:)
    assets = con.execute("""
        SELECT asset_id, space_id
        FROM main.dim_asset
    """).fetchdf()
    for _, r in assets.iterrows():
        rows.append({
            "canonical_id": f"asset:{r['asset_id']}",
            "system": "cafm",
            "native_id": r["asset_id"],
        })
        # Link asset to its space
        rows.append({
            "canonical_id": f"asset:{r['asset_id']}",
            "system": "space_register",
            "native_id": r["space_id"],
        })

    # 3. Buildings
    buildings = con.execute("SELECT building_id FROM main.dim_building").fetchdf()
    for _, r in buildings.iterrows():
        rows.append({
            "canonical_id": f"bldg:{r['building_id']}",
            "system": "space_register",
            "native_id": r["building_id"],
        })

    # 4. Meters
    meters = con.execute("SELECT meter_id, building_id FROM main.dim_meter").fetchdf()
    for _, r in meters.iterrows():
        rows.append({
            "canonical_id": f"meter:{r['meter_id']}",
            "system": "meter",
            "native_id": r["meter_id"],
        })
        rows.append({
            "canonical_id": f"meter:{r['meter_id']}",
            "system": "space_register",
            "native_id": r["building_id"],
        })

    # 5. Sensors
    sensors = con.execute("""
        SELECT s.sensor_id, s.space_id
        FROM main.stg_truth__sensor s
    """).fetchdf()
    for _, r in sensors.iterrows():
        rows.append({
            "canonical_id": f"sensor:{r['sensor_id']}",
            "system": "sensor",
            "native_id": r["sensor_id"],
        })
        rows.append({
            "canonical_id": f"sensor:{r['sensor_id']}",
            "system": "space_register",
            "native_id": r["space_id"],
        })

    # 6. BMS points (from stg_bms__trend point_id)
    bms_points = con.execute("""
        SELECT DISTINCT point_id FROM main.stg_bms__trend
    """).fetchdf()
    for _, r in bms_points.iterrows():
        rows.append({
            "canonical_id": f"bms_point:{r['point_id']}",
            "system": "bms",
            "native_id": r["point_id"],
        })

    # 7. IFC GlobalIds for spaces (from truth spaces parquet)
    import pyarrow.parquet as pq
    truth_spaces = pq.read_table('data/truth/spaces.parquet').to_pandas()
    ifc_map = dict(zip(truth_spaces['space_id'], truth_spaces['ifc_guid']))
    for space_id, ifc_guid in ifc_map.items():
        if pd.notna(ifc_guid):
            rows.append({
                "canonical_id": f"space:{space_id}",
                "system": "ifc",
                "native_id": ifc_guid,
            })

    # 8. Work orders (CAFM system)
    wo = con.execute("SELECT wo_id, asset_id FROM main.fct_work_order").fetchdf()
    for _, r in wo.iterrows():
        rows.append({
            "canonical_id": f"work_order:{r['wo_id']}",
            "system": "cafm",
            "native_id": r["wo_id"],
        })

    # 9. Timetable
    tt = con.execute("SELECT event_id, space_id FROM main.fct_timetable_event").fetchdf()
    for _, r in tt.iterrows():
        rows.append({
            "canonical_id": f"timetable:{r['event_id']}",
            "system": "timetable",
            "native_id": r["event_id"],
        })
        rows.append({
            "canonical_id": f"timetable:{r['event_id']}",
            "system": "space_register",
            "native_id": r["space_id"],
        })

    # 10. Inspections
    insp = con.execute("SELECT inspection_id, building_id FROM main.fct_inspection").fetchdf()
    for _, r in insp.iterrows():
        rows.append({
            "canonical_id": f"inspection:{r['inspection_id']}",
            "system": "inspection",
            "native_id": r["inspection_id"],
        })
        rows.append({
            "canonical_id": f"inspection:{r['inspection_id']}",
            "system": "space_register",
            "native_id": r["building_id"],
        })

    con.close()

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["canonical_id", "system", "native_id"])
    df = df.sort_values(["canonical_id", "system", "native_id"]).reset_index(drop=True)
    return df


def write_crosswalk(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "entity_crosswalk.parquet", index=False)
    df.to_csv(out_dir / "entity_crosswalk.csv", index=False)
    print(f"Crosswalk written: {len(df)} rows to {out_dir}")


def load_crosswalk(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)


if __name__ == "__main__":
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    df = build_crosswalk()
    write_crosswalk(df, out)
    print(df.head(20))
    print(f"\nUnique canonical IDs: {df['canonical_id'].nunique()}")
    print(f"Systems: {df['system'].unique()}")