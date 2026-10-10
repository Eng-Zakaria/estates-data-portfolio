"""The TimescaleDB schema.

The schema is applied by the database container on first boot and must be safe
to re-apply (a restart re-runs docker-entrypoint-initdb.d only on an empty
data directory, but an operator re-running it by hand is normal). These checks
read the SQL rather than needing a live database; `make iot-up` is what proves
the migration applies cleanly against a real TimescaleDB.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

SCHEMA = Path(__file__).resolve().parents[1] / "src" / "schema.sql"


@pytest.fixture(scope="module")
def sql() -> str:
    return SCHEMA.read_text(encoding="utf-8")


def _statements(sql: str) -> list[str]:
    """Split on semicolons, ignoring comments, so each DDL statement is checked."""
    without_comments = re.sub(r"--[^\n]*", "", sql)
    return [s.strip() for s in without_comments.split(";") if s.strip()]


# ---------------------------------------------------------------- tables
def test_schema_creates_the_four_documented_tables(sql):
    for table in ("bms.points", "bms.readings", "bms.dead_letter", "bms.alerts"):
        assert re.search(rf"CREATE TABLE IF NOT EXISTS {re.escape(table)}", sql), table


def test_readings_has_the_documented_columns(sql):
    block = re.search(r"CREATE TABLE IF NOT EXISTS bms\.readings \((.*?)\);", sql, re.S)
    assert block
    columns = block.group(1)
    for column, dtype in [
        ("ts", "TIMESTAMPTZ"),
        ("point_id", "TEXT"),
        ("value", "DOUBLE PRECISION"),
        ("unit", "TEXT"),
        ("quality", "TEXT"),
    ]:
        assert re.search(rf"\b{column}\s+{dtype}", columns), column


def test_points_registry_matches_the_csv_columns(sql):
    """The table and src/point_registry.csv must agree, or a message resolves to
    a point_id the database cannot key on."""
    block = re.search(r"CREATE TABLE IF NOT EXISTS bms\.points \((.*?)\);", sql, re.S)
    assert block
    for column in (
        "point_id",
        "building",
        "system",
        "equipment",
        "equipment_kind",
        "point_class",
        "unit",
        "source_address",
    ):
        assert re.search(rf"\b{column}\s", block.group(1)), column


def test_dead_letter_keeps_the_reason_code(sql):
    block = re.search(r"CREATE TABLE IF NOT EXISTS bms\.dead_letter \((.*?)\);", sql, re.S)
    assert "reason" in block.group(1)
    assert "payload" in block.group(1)


# ---------------------------------------------------------------- hypertables
def test_readings_is_a_hypertable_partitioned_on_time(sql):
    assert re.search(r"create_hypertable\(\s*'bms\.readings',\s*'ts'", sql)
    assert "if_not_exists => TRUE" in sql


def test_compression_is_configured_and_keyed_on_point_id(sql):
    assert "timescaledb.compress" in sql
    assert re.search(r"compress_segmentby\s*=\s*'point_id'", sql)


def test_compression_and_retention_policies_exist(sql):
    assert re.search(r"add_compression_policy\(\s*'bms\.readings'", sql)
    assert re.search(r"add_retention_policy\(\s*'bms\.readings'", sql)


def test_uniqueness_is_enforced_so_redelivery_is_idempotent(sql):
    assert re.search(r"CREATE UNIQUE INDEX.*readings_ts_point_uidx", sql, re.S)


# ---------------------------------------------------------------- aggregates
def test_three_continuous_aggregates_exist(sql):
    for view in ("bms.readings_15min", "bms.readings_hourly", "bms.readings_daily"):
        assert re.search(rf"CREATE MATERIALIZED VIEW IF NOT EXISTS {re.escape(view)}", sql), view
        assert re.search(rf"add_continuous_aggregate_policy\(\s*'{re.escape(view)}'", sql), view


def test_daily_aggregate_sums_energy_but_the_minute_ones_do_not(sql):
    """A sum of temperature is meaningless; a sum of kWh is the point of the
    daily rollup."""
    daily = re.search(r"CREATE MATERIALIZED VIEW IF NOT EXISTS bms\.readings_daily.*?;", sql, re.S)
    assert "SUM(value) AS sum_value" in daily.group(0)
    for view in ("bms.readings_15min", "bms.readings_hourly"):
        block = re.search(rf"CREATE MATERIALIZED VIEW IF NOT EXISTS {re.escape(view)}.*?;", sql, re.S)
        assert "SUM(value)" not in block.group(0), view


def test_aggregates_are_created_without_data_then_backfilled_by_policy(sql):
    """`WITH NO DATA` avoids a long migration; the refresh policy backfills."""
    assert sql.count("WITH NO DATA") == 3


def test_aggregate_refresh_windows_are_wider_than_the_source_interval(sql):
    assert re.search(
        r"add_continuous_aggregate_policy\(\s*'bms\.readings_15min'.*?end_offset => INTERVAL '15 minutes'", sql, re.S
    )
    assert re.search(
        r"add_continuous_aggregate_policy\(\s*'bms\.readings_hourly'.*?end_offset => INTERVAL '1 hour'", sql, re.S
    )


# ---------------------------------------------------------------- views
def test_grafana_views_exist(sql):
    for view in ("bms.v_latest_value", "bms.v_point_health", "bms.v_completeness"):
        assert re.search(rf"CREATE OR REPLACE VIEW {re.escape(view)}", sql), view


def test_point_health_view_covers_the_last_24_hours(sql):
    block = re.search(r"CREATE OR REPLACE VIEW bms\.v_point_health AS(.*?);", sql, re.S)
    assert "now() - INTERVAL '24 hours'" in block.group(1)


def test_completeness_view_groups_by_building_and_point_class(sql):
    """That grain is what the completeness heatmap reads."""
    block = re.search(r"CREATE OR REPLACE VIEW bms\.v_completeness AS(.*?);", sql, re.S)
    assert "GROUP BY p.building, p.point_class" in block.group(1)


# ---------------------------------------------------------------- idempotency
def test_every_statement_is_re_runnable(sql):
    """The container runs this file on first boot and an operator may re-apply
    it, so nothing may be a bare CREATE."""
    for statement in _statements(sql):
        if re.match(r"^CREATE TABLE", statement):
            assert "IF NOT EXISTS" in statement, statement[:80]
        if re.match(r"^CREATE (MATERIALIZED VIEW|UNIQUE INDEX|INDEX)", statement):
            assert "IF NOT EXISTS" in statement, statement[:80]


def test_policy_functions_are_all_idempotent_guarded(sql):
    for call in (
        "create_hypertable",
        "add_compression_policy",
        "add_retention_policy",
        "add_continuous_aggregate_policy",
    ):
        for match in re.finditer(rf"{call}\(.*?\);", sql, re.S):
            assert "if_not_exists => TRUE" in match.group(0), call


def test_alerts_keep_one_open_row_per_point_and_alert_type(sql):
    """Without the partial unique index a 5-minute staleness check would insert
    a duplicate alert row every cycle."""
    assert re.search(r"CREATE UNIQUE INDEX.*alerts_open_uidx.*WHERE resolved_at IS NULL", sql, re.S)


def test_extension_and_schema_are_created_if_missing(sql):
    assert "CREATE EXTENSION IF NOT EXISTS timescaledb" in sql
    assert "CREATE SCHEMA IF NOT EXISTS bms" in sql


def test_sql_parses_into_statements_without_leftover_junk(sql):
    statements = _statements(sql)
    assert len(statements) > 15
    for statement in statements:
        assert not statement.startswith("/*")
        assert statement.strip()


def test_no_secrets_in_the_schema(sql):
    for banned in ("password", "PASSWORD"):
        assert banned not in sql
