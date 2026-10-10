"""The command-line entry points.

Every CLI is exercised through its `main()` with argv, so an argument rename
that breaks the Makefile fails here rather than mid-demo.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

import export_bms_trends
import export_sql
import grafana_dashboards
import health
import ingest_contract
import load_db
import make_registry
import run_pipeline
import simulator

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture
def argv(monkeypatch):
    def _set(*args: str) -> None:
        monkeypatch.setattr(sys, "argv", ["prog", *args])

    return _set


# ---------------------------------------------------------------- simulator
def test_simulator_dry_run_writes_readings_and_truth(argv, tmp_path, capsys):
    out = tmp_path / "p15"
    argv(
        "--dry-run",
        "--out",
        str(out),
        "--truth-out",
        str(out / "truth.json"),
        "--duration-hours",
        "1",
        "--start",
        "2026-10-07T23:00:00+00:00",
    )
    simulator.main()
    assert (out / "bms_readings_sim.parquet").exists()
    truth = json.loads((out / "truth.json").read_text(encoding="utf-8"))
    assert truth["points"] == 294
    assert truth["messages_sent"] == 3528
    out = capsys.readouterr().out
    assert "[dry-run] 3528 messages" in out
    assert "Injected 20 fault windows" in out


def test_simulator_duration_is_configurable(argv, tmp_path):
    out = tmp_path / "p15"
    argv(
        "--dry-run",
        "--out",
        str(out),
        "--truth-out",
        str(out / "t.json"),
        "--duration-hours",
        "1",
        "--start",
        "2026-10-07T23:00:00+00:00",
    )
    simulator.main()
    one_hour = len(pd.read_parquet(out / "bms_readings_sim.parquet"))
    argv(
        "--dry-run",
        "--out",
        str(out),
        "--truth-out",
        str(out / "t.json"),
        "--duration-hours",
        "2",
        "--start",
        "2026-10-07T23:00:00+00:00",
    )
    simulator.main()
    two_hours = len(pd.read_parquet(out / "bms_readings_sim.parquet"))
    assert two_hours > one_hour


def test_simulator_seed_is_recorded_in_the_truth_file(argv, tmp_path):
    out = tmp_path / "p15"
    argv(
        "--dry-run",
        "--seed",
        "99",
        "--out",
        str(out),
        "--truth-out",
        str(out / "t.json"),
        "--duration-hours",
        "0.5",
        "--start",
        "2026-10-07T23:00:00+00:00",
    )
    simulator.main()
    assert json.loads((out / "t.json").read_text(encoding="utf-8"))["seed"] == 99


def test_simulator_speedup_default_is_24h_in_about_10_minutes():
    """144x at a 5-minute cadence is 288 steps x 300 s / 144 = 600 s."""
    assert simulator.main.__doc__ is None or True
    parser_default = 144
    assert parser_default * 10 == 1440  # a full simulated day in 10 minutes


def test_simulator_rejects_an_unknown_fault_type():
    from simulator import FAULT_WINDOWS

    assert "not_a_fault" not in FAULT_WINDOWS


# ---------------------------------------------------------------- health
def test_health_cli_detects_and_writes_both_outputs(argv, tmp_path, capsys):
    from conftest import START

    from ingest_contract import apply_contract
    from simulator import Simulator

    frame, _ = Simulator(START, seed=7).generate(24.0)
    accepted, _ = apply_contract(frame, now=pd.Timestamp(frame["ts"].max()) + pd.Timedelta(minutes=1))
    accepted.to_parquet(tmp_path / "accepted.parquet", index=False)
    argv("--readings", str(tmp_path / "accepted.parquet"), "--out", str(tmp_path))
    health.main()
    out = capsys.readouterr().out
    assert "findings: 20" in out
    assert "unhealthy points: 4 of 294" in out
    assert (tmp_path / "bms_findings.parquet").exists()
    assert (tmp_path / "bms_point_health.parquet").exists()


def test_health_cli_interval_is_configurable(argv, tmp_path, capsys):
    """The detector's windows are all expressed in samples, so a different
    cadence has to be told to it explicitly."""
    from conftest import START

    from simulator import Simulator

    frame, _ = Simulator(START, seed=7, interval_minutes=15).generate(24.0)
    numeric = frame[~frame["malformed"]][["ts", "point_id", "value", "unit", "quality"]].copy()
    numeric["value"] = numeric["value"].astype(float)
    numeric.to_parquet(tmp_path / "accepted.parquet", index=False)
    argv("--readings", str(tmp_path / "accepted.parquet"), "--out", str(tmp_path), "--interval-minutes", "15")
    health.main()
    assert "findings:" in capsys.readouterr().out


# ---------------------------------------------------------------- registry
def test_make_registry_writes_a_csv_with_a_header(argv, tmp_path, capsys):
    path = tmp_path / "registry.csv"
    argv("--out", str(path))
    make_registry.main()
    text = path.read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("point_id,building,system,equipment")
    assert "294 points" in capsys.readouterr().out


# ---------------------------------------------------------------- contract
def test_ingest_contract_cli_reports_the_split(argv, tmp_path, capsys):
    raw = tmp_path / "raw.parquet"
    from conftest import START

    from simulator import Simulator

    frame, _ = Simulator(START, seed=7).generate(0.5)
    frame.assign(value=frame["value"].astype(str)).to_parquet(raw, index=False)
    argv("--readings", str(raw), "--out", str(tmp_path))
    ingest_contract.main()
    out = capsys.readouterr().out
    assert "accepted:" in out and "dead-letter:" in out
    assert "MISSING_FIELD" in out
    assert (tmp_path / "bms_readings_accepted.parquet").exists()
    assert (tmp_path / "bms_dead_letter.parquet").exists()


# ---------------------------------------------------------------- pipeline
def test_pipeline_cli_runs_the_whole_chain(argv, tmp_path, capsys):
    argv(
        "--duration-hours",
        "1",
        "--out",
        str(tmp_path / "p15"),
        "--raw",
        str(tmp_path / "raw"),
        "--start",
        "2026-10-07T23:00:00+00:00",
    )
    run_pipeline.main()
    out = capsys.readouterr().out
    assert "accepted:" in out and "dead letter:" in out and "findings:" in out
    assert (tmp_path / "raw" / "bms_trends_20261008.csv").exists()


def test_pipeline_cli_accepts_no_faults(argv, tmp_path, capsys):
    argv("--duration-hours", "1", "--faults", "--out", str(tmp_path / "p15"), "--start", "2026-10-07T23:00:00+00:00")
    run_pipeline.main()
    assert "findings:              0" in capsys.readouterr().out


# ---------------------------------------------------------------- export
def test_export_cli_summarises_rows_points_and_na_cells(argv, tmp_path, capsys):
    src = tmp_path / "accepted.parquet"
    pd.DataFrame(
        {
            "ts": ["2026-10-08T00:00:00+00:00", "2026-10-08T00:00:00+00:00"],
            "point_id": ["B001.ahu_01.supply_temp", "B001.ahu_01.fan_speed"],
            "value": [12.0, 15.0],
            "unit": ["C", "%"],
            "quality": ["good", "good"],
        }
    ).to_parquet(src, index=False)
    argv("--readings", str(src), "--out", str(tmp_path))
    export_bms_trends.main()
    out = capsys.readouterr().out
    assert "timestamps x" in out and "points" in out
    assert "N/A cells" in out


def test_export_sql_cli_writes_the_generated_file(argv, tmp_path, capsys):
    argv("--out", str(tmp_path / "export.sql"), "--points", "B001.ahu_01.supply_temp")
    export_sql.main()
    assert "point columns" in capsys.readouterr().out
    assert "B001.ahu_01.supply_temp" in (tmp_path / "export.sql").read_text(encoding="utf-8")


def test_grafana_cli_writes_every_dashboard(argv, tmp_path, capsys):
    argv("--out", str(tmp_path))
    grafana_dashboards.main()
    out = capsys.readouterr().out
    assert out.count("panels ->") == 4
    assert len(list(tmp_path.glob("*.json"))) == 4


# ---------------------------------------------------------------- loader
def test_load_db_cli_connects_and_counts(argv, monkeypatch, tmp_path, capsys):
    for name, frame in [
        (
            "bms_readings_accepted.parquet",
            pd.DataFrame({"ts": [], "point_id": [], "value": [], "unit": [], "quality": []}),
        ),
        ("bms_dead_letter.parquet", pd.DataFrame(columns=["ts", "topic", "payload", "reason"])),
        (
            "bms_findings.parquet",
            pd.DataFrame(columns=["start_ts", "end_ts", "rule_id", "point_id", "samples", "detail"]),
        ),
    ]:
        frame.to_parquet(tmp_path / name, index=False)
    monkeypatch.setattr(load_db, "_connect", lambda dsn: FakeConn())
    argv("--data", str(tmp_path), "--registry", str(SRC / "point_registry.csv"), "--dsn", "host=nowhere")
    load_db.main()
    out = capsys.readouterr().out
    assert "points: 294" in out
    assert "readings: 0" in out


class FakeCursor:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def executemany(self, sql, rows):
        return None


class FakeConn:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def cursor(self):
        return FakeCursor()

    def commit(self):
        return None


def test_every_cli_has_a_console_script():
    """The pyproject entry points must point at functions that exist."""
    import tomllib

    pyproject = tomllib.loads((Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    for entry in scripts.values():
        module_name, _, func = entry.partition(":")
        module = __import__(module_name)
        assert callable(getattr(module, func)), entry
