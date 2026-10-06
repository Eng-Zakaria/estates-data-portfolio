"""Compute twin_coverage report (P18)."""

from __future__ import annotations

import duckdb
import pyarrow.parquet as pq


def compute_coverage() -> dict:
    """Compute cross-system coverage metrics."""
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)

    # 1. % assets with IFC GlobalId (from truth parquet)
    truth_assets = pq.read_table('data/truth/assets.parquet').to_pandas()
    asset_ifc = (truth_assets['ifc_guid'].notna() & (truth_assets['ifc_guid'] != '')).sum()
    total_assets = con.execute("SELECT COUNT(*) FROM main.dim_asset").fetchone()[0]
    assets_with_ifc_pct = (asset_ifc / total_assets * 100) if total_assets else 0

    # 2. % spaces with sensors
    spaces_with_sensors = con.execute("""
        SELECT COUNT(DISTINCT space_id) FROM main.stg_truth__sensor
    """).fetchone()[0]
    total_spaces = con.execute("SELECT COUNT(*) FROM main.dim_space").fetchone()[0]
    spaces_with_sensors_pct = (spaces_with_sensors / total_spaces * 100) if total_spaces else 0

    # 3. % assets linked to a BMS point
    assets_bms = con.execute("""
        SELECT COUNT(DISTINCT a.asset_id)
        FROM main.dim_asset a
        JOIN main.stg_truth__sensor s ON s.space_id = a.space_id
        JOIN main.stg_bms__trend b ON b.point_id LIKE s.sensor_id || ' %'
    """).fetchone()[0]
    total_assets2 = con.execute("SELECT COUNT(*) FROM main.dim_asset").fetchone()[0]
    assets_linked_to_bms_pct = (assets_bms / total_assets2 * 100) if total_assets2 else 0

    # 4. % meters mapped to a building
    meters_mapped = con.execute(
        "SELECT COUNT(*) FROM main.dim_meter WHERE building_id IS NOT NULL"
    ).fetchone()[0]
    total_meters = con.execute("SELECT COUNT(*) FROM main.dim_meter").fetchone()[0]
    meters_mapped_to_building_pct = (meters_mapped / total_meters * 100) if total_meters else 0

    con.close()

    return {
        "assets_with_ifc_guid_pct": round(assets_with_ifc_pct, 2),
        "spaces_with_sensors_pct": round(spaces_with_sensors_pct, 2),
        "assets_linked_to_bms_pct": round(assets_linked_to_bms_pct, 2),
        "meters_mapped_to_building_pct": round(meters_mapped_to_building_pct, 2),
    }


if __name__ == "__main__":
    print(compute_coverage())