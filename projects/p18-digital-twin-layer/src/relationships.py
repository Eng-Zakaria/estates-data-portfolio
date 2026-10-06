"""Build relationship graph with Brick-aligned predicates (P18).

relationship (subject_id, predicate, object_id, source, valid_from, valid_to)

Brick predicates used:
- hasPart (building → space, asset → point)
- isLocatedIn (space → building, asset → space, sensor → space)
- feeds (AHU → terminal unit, meter → building)
- hasPoint (asset → sensor/bms_point, AHU → point)
- isMeteredBy (space/building → meter)
- isServedBy (space → AHU)
"""

from __future__ import annotations

from pathlib import Path
from datetime import date

import duckdb
import pandas as pd


def build_relationships() -> pd.DataFrame:
    """Build the relationship graph from gold marts and crosswalk."""
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    rows = []

    # 1. Building hasPart Space
    spaces = con.execute("SELECT building_id, space_id FROM main.dim_space").fetchdf()
    for _, r in spaces.iterrows():
        rows.append({
            "subject_id": f"bldg:{r['building_id']}",
            "predicate": "hasPart",
            "object_id": f"space:{r['space_id']}",
            "source": "space_register",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 2. Space isLocatedIn Building
    for _, r in spaces.iterrows():
        rows.append({
            "subject_id": f"space:{r['space_id']}",
            "predicate": "isLocatedIn",
            "object_id": f"bldg:{r['building_id']}",
            "source": "space_register",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 3. Asset isLocatedIn Space
    assets = con.execute("SELECT asset_id, space_id FROM main.dim_asset").fetchdf()
    for _, r in assets.iterrows():
        rows.append({
            "subject_id": f"asset:{r['asset_id']}",
            "predicate": "isLocatedIn",
            "object_id": f"space:{r['space_id']}",
            "source": "cafm",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 4. Building hasPart Asset (via space -> building)
    asset_spaces = con.execute("""
        SELECT a.asset_id, s.building_id
        FROM main.dim_asset a
        JOIN main.dim_space s ON s.space_id = a.space_id
    """).fetchdf()
    for _, r in asset_spaces.iterrows():
        rows.append({
            "subject_id": f"bldg:{r['building_id']}",
            "predicate": "hasPart",
            "object_id": f"asset:{r['asset_id']}",
            "source": "cafm",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 5. Meter isMeteredBy Building
    meters = con.execute("SELECT meter_id, building_id FROM main.dim_meter").fetchdf()
    for _, r in meters.iterrows():
        rows.append({
            "subject_id": f"bldg:{r['building_id']}",
            "predicate": "isMeteredBy",
            "object_id": f"meter:{r['meter_id']}",
            "source": "meter",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 6. Sensor isLocatedIn Space
    sensors = con.execute("SELECT sensor_id, space_id FROM main.stg_truth__sensor").fetchdf()
    for _, r in sensors.iterrows():
        rows.append({
            "subject_id": f"sensor:{r['sensor_id']}",
            "predicate": "isLocatedIn",
            "object_id": f"space:{r['space_id']}",
            "source": "sensor",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 7. Asset hasPoint Sensor (synthetic mapping: same space)
    for _, r in sensors.iterrows():
        # Find assets in same space
        assets_in_space = con.execute("""
            SELECT asset_id FROM main.dim_asset WHERE space_id = ?
        """, [r['space_id']]).fetchdf()
        for _, a in assets_in_space.iterrows():
            rows.append({
                "subject_id": f"asset:{a['asset_id']}",
                "predicate": "hasPoint",
                "object_id": f"sensor:{r['sensor_id']}",
                "source": "sensor",
                "valid_from": date(2026, 1, 1),
                "valid_to": None,
            })

    # 8. BMS point hasPoint Asset (synthetic: map by space)
    # BMS point_id format: "SN-XXXX [ppm/°C/%]" - map to sensor by prefix
    bms = con.execute("SELECT DISTINCT point_id FROM main.stg_bms__trend").fetchdf()
    for _, r in bms.iterrows():
        point_id = r['point_id']
        sensor_prefix = point_id.split(" ")[0]  # e.g., "SN-0001"
        # Find matching sensor
        sensor = con.execute("""
            SELECT sensor_id, space_id FROM main.stg_truth__sensor
            WHERE sensor_id = ?
        """, [sensor_prefix]).fetchdf()
        if not sensor.empty:
            s = sensor.iloc[0]
            # Find asset in same space (first one)
            asset = con.execute("""
                SELECT asset_id FROM main.dim_asset WHERE space_id = ? LIMIT 1
            """, [s['space_id']]).fetchdf()
            if not asset.empty:
                a = asset.iloc[0]
                rows.append({
                    "subject_id": f"asset:{a['asset_id']}",
                    "predicate": "hasPoint",
                    "object_id": f"bms_point:{point_id}",
                    "source": "bms",
                    "valid_from": date(2026, 1, 1),
                    "valid_to": None,
                })
            # Also link bms_point to space
            rows.append({
                "subject_id": f"bms_point:{point_id}",
                "predicate": "isLocatedIn",
                "object_id": f"space:{s['space_id']}",
                "source": "bms",
                "valid_from": date(2026, 1, 1),
                "valid_to": None,
            })

    # 9. AHU feeds Space (synthetic: AHU assets feed spaces they're in)
    ahu_assets = con.execute("""
        SELECT asset_id, space_id FROM main.dim_asset
        WHERE asset_type IN ('AHU', 'AHU Controller', 'BMS Controller')
    """).fetchdf()
    for _, r in ahu_assets.iterrows():
        rows.append({
            "subject_id": f"asset:{r['asset_id']}",
            "predicate": "feeds",
            "object_id": f"space:{r['space_id']}",
            "source": "cafm",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })
        # Space isServedBy AHU
        rows.append({
            "subject_id": f"space:{r['space_id']}",
            "predicate": "isServedBy",
            "object_id": f"asset:{r['asset_id']}",
            "source": "cafm",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 10. Timetable event isLocatedIn Space
    events = con.execute("SELECT event_id, space_id FROM main.fct_timetable_event").fetchdf()
    for _, r in events.iterrows():
        rows.append({
            "subject_id": f"timetable:{r['event_id']}",
            "predicate": "isLocatedIn",
            "object_id": f"space:{r['space_id']}",
            "source": "timetable",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    # 11. Work order isLocatedIn Asset
    events = con.execute("SELECT wo_id, asset_id FROM main.fct_work_order").fetchdf()
    for _, r in events.iterrows():
        rows.append({
            "subject_id": f"work_order:{r['wo_id']}",
            "predicate": "isLocatedIn",
            "object_id": f"asset:{r['asset_id']}",
            "source": "cafm",
            "valid_from": date(2026, 1, 1),
            "valid_to": None,
        })

    con.close()

    df = pd.DataFrame(rows)
    df = df.drop_duplicates().sort_values(
        ["subject_id", "predicate", "object_id"]
    ).reset_index(drop=True)
    return df


def write_relationships(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_dir / "relationship.parquet", index=False)
    df.to_csv(out_dir / "relationship.csv", index=False)
    print(f"Relationships written: {len(df)} rows to {out_dir}")


if __name__ == "__main__":
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    df = build_relationships()
    write_relationships(df, out)
    print(df.head(20))
    print(f"\nPredicates: {df['predicate'].unique()}")
    print(f"Sources: {df['source'].unique()}")
    print(f"Total: {len(df)}")