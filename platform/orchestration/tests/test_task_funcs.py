"""P02 unit tests for pure task logic (no airflow import; runs on any host)."""

from __future__ import annotations

import duckdb
import pandas as pd
from tasks.pipeline import (
    check_schema_drift,
    contract_columns,
    housekeeping,
    load_watermark,
    new_files_since,
    ops_connect,
    quarantine_landing_file,
    record_run,
    save_watermark,
    send_alert,
)


def _write_csv(path, columns, rows=2):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{c: "x" for c in columns} for _ in range(rows)]).to_csv(path, index=False)
    return str(path)


def test_schema_drift_clean(tmp_path):
    cols = contract_columns("cafm_workorders")
    path = _write_csv(tmp_path / "cafm_workorders_demo.csv", cols)
    report = check_schema_drift("cafm_workorders", path)
    assert report["drift"] is False
    assert report["added"] == [] and report["missing"] == []


def test_schema_drift_detects_extra_column(tmp_path):
    cols = contract_columns("cafm_workorders") + ["Mystery_Column"]
    path = _write_csv(tmp_path / "cafm_workorders_weird.csv", cols)
    report = check_schema_drift("cafm_workorders", path)
    assert report["drift"] is True
    assert report["added"] == ["Mystery_Column"]


def test_schema_drift_unreadable_file(tmp_path):
    missing = str(tmp_path / "nope.csv")
    report = check_schema_drift("cafm_workorders", missing)
    assert report["drift"] is True
    assert "error" in report


def test_quarantine_moves_file_and_writes_reason(tmp_path, monkeypatch):
    import tasks.pipeline as pipe

    monkeypatch.setattr(pipe, "LAKE", tmp_path / "lake")
    src = tmp_path / "cafm_workorders_bad.csv"
    src.write_text("a,b\n1,2\n", encoding="utf-8")
    dest = quarantine_landing_file("cafm_workorders", str(src), "test reason")
    assert not src.exists()
    reason_files = list((tmp_path / "lake" / "quarantine_files" / "cafm_workorders").glob("*.reason.txt"))
    assert len(reason_files) == 1 and "test reason" in reason_files[0].read_text()
    assert dest.endswith(".csv")


def test_watermark_roundtrip_and_new_files(tmp_path, monkeypatch):
    import tasks.pipeline as pipe

    monkeypatch.setattr(pipe, "LAKE", tmp_path / "lake")
    landing = tmp_path / "landing"
    monkeypatch.setattr(pipe, "LANDING", landing)
    landing.mkdir()
    (landing / "cafm_workorders_001.csv").write_text("a\n1\n", encoding="utf-8")
    wm = load_watermark("cafm_workorders")
    assert new_files_since("cafm_workorders", wm, landing) != []
    save_watermark(
        "cafm_workorders", {"source": "cafm_workorders", "files": [str(landing / "cafm_workorders_001.csv")]}
    )
    wm2 = load_watermark("cafm_workorders")
    assert new_files_since("cafm_workorders", wm2, landing) == []


def test_ops_store_records_runs(tmp_path):
    # NOTE: db filename must not stem to `ops` (DuckDB catalog/schema clash
    # with the ops.pipeline_runs schema name).
    db = tmp_path / "pipeline_ops.duckdb"
    record_run(
        {
            "dag_id": "d",
            "task_id": "t",
            "run_id": "r1",
            "data_interval_start": "2026-01-01",
            "status": "success",
            "duration_s": 1.5,
            "rows_in": 10,
            "rows_out": 9,
            "error": None,
        },
        db,
    )
    con = duckdb.connect(str(db), read_only=True)
    try:
        rows = con.execute("SELECT dag_id, status, rows_in FROM ops.pipeline_runs").fetchall()
    finally:
        con.close()
    assert rows == [("d", "success", 10)]


def test_ops_connect_idempotent(tmp_path):
    db = tmp_path / "pipeline_ops.duckdb"
    ops_connect(db).close()
    ops_connect(db).close()  # second open must not fail on existing schema/table


def test_send_alert_never_raises_on_bad_host(monkeypatch):
    import tasks.pipeline as pipe

    monkeypatch.setattr(pipe, "MAIL_HOST", "invalid-hostname-that-does-not-exist.local")
    assert send_alert("subject", "body") is False


def test_housekeeping_archives_old_files(tmp_path, monkeypatch):
    import os
    import time

    import tasks.pipeline as pipe

    landing = tmp_path / "landing"
    lake = tmp_path / "lake"
    monkeypatch.setattr(pipe, "LANDING", landing)
    monkeypatch.setattr(pipe, "LAKE", lake)
    landing.mkdir()
    old = landing / "old.csv"
    old.write_text("a\n1\n", encoding="utf-8")
    ancient = time.time() - 40 * 86400
    os.utime(old, (ancient, ancient))
    result = housekeeping(landing=landing, lake=lake, db_path=tmp_path / "pipeline_ops.duckdb")
    assert result["archived_landing_files"] == 1
    assert not old.exists()
    assert (lake / "archive" / "old.csv").exists()
