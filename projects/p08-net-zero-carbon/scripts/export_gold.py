"""Export P04 gold marts from warehouse.duckdb to data/gold/*.parquet.

Shared extract layer for the dashboard projects (P06-P10 Power BI handoff).
Re-run after `make dbt-build`. All data synthetic.
"""

from __future__ import annotations

import sys
from pathlib import Path

TABLES = [
    "dim_building",
    "dim_space",
    "dim_asset",
    "dim_department",
    "dim_meter",
    "dim_date",
    "dim_inspection_type",
    "dim_trade",
    "dim_emission_factor",
    "fct_meter_hh",
    "fct_energy_daily",
    "fct_work_order",
    "fct_inspection",
    "fct_timetable_event",
    "fct_sensor_15min",
    "fct_space_observed_occupancy",
    "mart_space_utilisation",
    "mart_asset_health",
    "mart_carbon_monthly",
    "mart_compliance_status",
    "mart_dq_scorecard",
]


def main(out: str = "data/gold") -> int:
    import duckdb

    dest = Path(out)
    dest.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    for table in TABLES:
        n = con.execute(f"SELECT COUNT(*) FROM main.{table}").fetchone()[0]
        con.execute(f"COPY (SELECT * FROM main.{table}) TO '{dest}/{table}.parquet' (FORMAT PARQUET)")
        print(f"{table}: {n} rows -> {dest}/{table}.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(*sys.argv[1:]))
