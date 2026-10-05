"""P03 result store: DuckDB database with dq.* tables + view registry for checks.

Checks read through named views (``silver_<dataset>``, ``quarantine_<dataset>``,
``truth_<table>``, ``defects``) registered on a query connection, so check SQL
stays portable across profiles and clean/defect runs. Results land in
``data/quality.duckdb`` (separate file from the warehouse: DuckDB takes one
writer per file, and dbt may hold the warehouse open).
"""

from __future__ import annotations

from pathlib import Path

import duckdb

TRUTH_TABLES = [
    "assets",
    "buildings",
    "departments",
    "meters",
    "inspection_types",
    "sensors",
    "spaces",
    "academic_calendar",
]

RESULTS_DDL = """
CREATE SCHEMA IF NOT EXISTS dq;
CREATE TABLE IF NOT EXISTS dq.runs (
    run_id VARCHAR PRIMARY KEY,
    ts_utc TIMESTAMPTZ,
    profile VARCHAR,
    label VARCHAR
);
CREATE TABLE IF NOT EXISTS dq.results (
    run_id VARCHAR,
    dataset VARCHAR,
    check_id VARCHAR,
    dimension VARCHAR,
    severity VARCHAR,
    engine VARCHAR,
    rows_checked BIGINT,
    rows_failed BIGINT,
    pass_rate DOUBLE,
    threshold DOUBLE,
    status VARCHAR
);
CREATE TABLE IF NOT EXISTS dq.failed_rows (
    run_id VARCHAR,
    check_id VARCHAR,
    sample_kind VARCHAR,
    row_json VARCHAR
);
CREATE TABLE IF NOT EXISTS dq.scores (
    run_id VARCHAR,
    grain VARCHAR,
    dataset VARCHAR,
    key VARCHAR,
    score DOUBLE,
    n_checks BIGINT
);
CREATE TABLE IF NOT EXISTS dq.alerts (
    run_id VARCHAR,
    alert_kind VARCHAR,
    dataset VARCHAR,
    detail VARCHAR
);
"""


def connect(store: str | Path, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    Path(store).parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(store), read_only=read_only)
    if not read_only:
        con.execute(RESULTS_DDL)
    return con


def register_views(
    con: duckdb.DuckDBPyConnection,
    lake: str | Path,
    truth: str | Path,
    ground_truth: str | Path | None = None,
    snap: str | Path | None = None,
) -> None:
    """Register silver/quarantine/truth/defect views used by check SQL."""
    lake_p, truth_p = Path(lake), Path(truth)
    for dataset, sub in [
        ("spaces", "space_register"),
        ("work_orders", "cafm_workorders"),
        ("meters_a", "meter_hh_supplierA"),
        ("meters_b", "meter_hh_supplierB"),
        ("sensors", "sensors"),
        ("bms", "bms_trends"),
        ("inspections", "statutory_inspections"),
        ("timetable", "timetable"),
    ]:
        con.execute(
            f"CREATE OR REPLACE VIEW silver_{dataset} AS "
            f"SELECT * FROM read_parquet('{lake_p}/silver/{sub}/silver.parquet')"
        )
        con.execute(
            f"CREATE OR REPLACE VIEW quarantine_{dataset} AS "
            f"SELECT * FROM read_parquet('{lake_p}/quarantine/{sub}/quarantine.parquet')"
        )
    for table in TRUTH_TABLES:
        con.execute(f"CREATE OR REPLACE VIEW truth_{table} AS SELECT * FROM read_parquet('{truth_p}/{table}.parquet')")
    if ground_truth is not None:
        import pandas as pd
        import yaml

        with open(ground_truth, encoding="utf-8") as f:
            defects = yaml.safe_load(f)["defects"]
        con.register(
            "defects_df",
            pd.DataFrame(defects)[["table", "type", "row_key"]],
        )
        con.execute("CREATE OR REPLACE VIEW defects AS SELECT * FROM defects_df")
    if snap is not None:
        con.execute(
            "CREATE OR REPLACE VIEW silver_spaces_snapshot AS "
            f"SELECT * FROM read_parquet('{Path(snap)}/spaces.parquet')"
        )
