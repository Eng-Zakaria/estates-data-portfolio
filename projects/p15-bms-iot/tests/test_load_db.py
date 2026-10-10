"""The database loader: the SQL it sends and the idempotency it relies on.

No live database is needed: a recording cursor captures the statements, and the
tests assert the upsert clauses that make re-running the loader safe.
"""

from __future__ import annotations

import pandas as pd
import pytest
from conftest import REGISTRY_CSV

import load_db


class RecordingCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, list]] = []

    def __enter__(self) -> RecordingCursor:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def executemany(self, sql: str, rows: list) -> None:
        self.calls.append((sql, list(rows)))


class RecordingConn:
    def __init__(self) -> None:
        self.cur = RecordingCursor()

    def __enter__(self) -> RecordingConn:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def cursor(self) -> RecordingCursor:
        return self.cur

    def commit(self) -> None:
        return None


@pytest.fixture
def conn() -> RecordingConn:
    return RecordingConn()


def _accepted() -> pd.DataFrame:
    base = pd.Timestamp("2026-10-07T23:00:00+00:00")
    return pd.DataFrame(
        {
            "ts": [base.isoformat(), base.isoformat()],
            "point_id": ["B001.ahu_01.supply_temp", "B001.ahu_01.fan_speed"],
            "value": [12.0, 15.0],
            "unit": ["C", "%"],
            "quality": ["good", "suspect"],
        }
    )


def test_points_are_upserted_not_inserted(conn):
    assert load_db.load_points(conn, REGISTRY_CSV) == 294
    sql, rows = conn.cur.calls[0]
    assert "ON CONFLICT (point_id) DO UPDATE" in sql
    assert rows[0][0] == "B001.ahu_01.cooling_valve"
    # the full registry row, in the order the table declares
    assert len(rows[0]) == 8


def test_readings_upsert_on_the_unique_key(conn):
    assert load_db.load_readings(conn, _accepted()) == 2
    sql, rows = conn.cur.calls[0]
    assert "ON CONFLICT (ts, point_id) DO UPDATE" in sql
    assert rows[0][1] == "B001.ahu_01.supply_temp"


def test_reloading_the_same_readings_is_idempotent(conn):
    """At-least-once delivery means the same (ts, point_id) arrives twice; the
    unique index plus ON CONFLICT keeps one row."""
    load_db.load_readings(conn, _accepted())
    load_db.load_readings(conn, _accepted())
    assert len(conn.cur.calls) == 2
    assert all("ON CONFLICT (ts, point_id)" in sql for sql, _ in conn.cur.calls)


def test_dead_letter_rows_carry_topic_payload_and_reason(conn):
    dead = pd.DataFrame(
        {
            "ts": ["2026-10-07T23:00:00+00:00"],
            "topic": ["campus/B001/ahu/ahu_01/supply_temp"],
            "payload": ['{"value": "nope"}'],
            "reason": ["MISSING_FIELD"],
        }
    )
    assert load_db.load_dead_letter(conn, dead) == 1
    sql, rows = conn.cur.calls[0]
    assert "bms.dead_letter" in sql
    assert rows[0][3] == "MISSING_FIELD"


def test_empty_dead_letter_sends_nothing(conn):
    empty = pd.DataFrame(columns=["ts", "topic", "payload", "reason"])
    assert load_db.load_dead_letter(conn, empty) == 0
    assert conn.cur.calls == []


def test_findings_are_upserted(conn):
    findings = pd.DataFrame(
        {
            "start_ts": [pd.Timestamp("2026-10-08T01:00:00+00:00")],
            "end_ts": [pd.Timestamp("2026-10-08T05:00:00+00:00")],
            "rule_id": ["SEM-02"],
            "point_id": ["B001.ahu_01.heating_valve"],
            "samples": [60],
            "detail": ["valve constant at 62% for 60 samples"],
        }
    )
    assert load_db.load_findings(conn, findings) == 1
    sql, rows = conn.cur.calls[0]
    assert "ON CONFLICT (start_ts, rule_id, point_id)" in sql
    assert rows[0][2] == "SEM-02"


def test_findings_target_objects_the_schema_creates(project):
    """bms.findings was added to schema.sql for the dashboards; if the migration
    stops creating it the loader fails at runtime."""
    schema = (project / "src" / "schema.sql").read_text(encoding="utf-8")
    for table in ("bms.readings", "bms.points", "bms.dead_letter", "bms.findings"):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema, table


def test_dsn_defaults_match_the_documented_host_port(monkeypatch):
    for key in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD"):
        monkeypatch.delenv(key, raising=False)
    dsn = load_db.dsn_from_env()
    assert "port=5433" in dsn, "the demo stack is published on 5433, not 5432"
    assert "dbname=bms_db" in dsn


def test_dsn_reads_the_environment(monkeypatch):
    monkeypatch.setenv("PGPORT", "6000")
    monkeypatch.setenv("PGDATABASE", "other")
    dsn = load_db.dsn_from_env()
    assert "port=6000" in dsn
    assert "dbname=other" in dsn


def test_load_all_reads_the_pipeline_outputs(tmp_path, monkeypatch):
    for name, frame in [
        ("bms_readings_accepted.parquet", _accepted()),
        ("bms_dead_letter.parquet", pd.DataFrame(columns=["ts", "topic", "payload", "reason"])),
        (
            "bms_findings.parquet",
            pd.DataFrame(columns=["start_ts", "end_ts", "rule_id", "point_id", "samples", "detail"]),
        ),
    ]:
        frame.to_parquet(tmp_path / name, index=False)
    monkeypatch.setattr(load_db, "_connect", lambda dsn: RecordingConn())
    counts = load_db.load_all(tmp_path, REGISTRY_CSV, "host=nowhere")
    assert counts == {"points": 294, "readings": 2, "dead_letter": 0, "findings": 0}


def test_every_statement_targets_a_bms_table(conn):
    load_db.load_points(conn, REGISTRY_CSV)
    load_db.load_readings(conn, _accepted())
    for sql, _ in conn.cur.calls:
        assert "bms." in sql
