"""Determinism of the CLI entry points.

Every number in the README comes from running the CLIs, so a run that gives
different results depending on the wall clock or the working directory would
make the documented figures unreproducible.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import ingest_contract
import simulator

SRC = Path(__file__).resolve().parents[1] / "src"


@pytest.fixture
def argv(monkeypatch):
    def _set(*args: str) -> None:
        monkeypatch.setattr("sys.argv", ["prog", *args])

    return _set


def _simulate(argv, tmp_path: Path, *extra: str) -> tuple[Path, Path]:
    out = tmp_path / "p15"
    argv(
        "--dry-run",
        "--duration-hours",
        "2",
        "--out",
        str(out),
        "--truth-out",
        str(out / "truth.json"),
        *extra,
    )
    simulator.main()
    return out, out / "truth.json"


def test_cli_defaults_start_at_local_midnight(argv, tmp_path):
    """Fault windows are minutes from the run start, so a start of "now" would
    move every window and change the detection metrics run to run."""
    out, truth_path = _simulate(argv, tmp_path)
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    start = pd.Timestamp(truth["start"])
    local = start.tz_convert("Europe/London")
    assert local.hour == 0
    assert local.minute == 0


def test_cli_start_flag_overrides_the_default(argv, tmp_path):
    _out, truth_path = _simulate(argv, tmp_path, "--start", "2026-03-04T00:00:00+00:00")
    assert pd.Timestamp(json.loads(truth_path.read_text(encoding="utf-8"))["start"]) == pd.Timestamp(
        "2026-03-04T00:00:00+00:00"
    )


def test_two_runs_of_the_cli_produce_identical_output(argv, tmp_path):
    first, _ = _simulate(argv, tmp_path / "a")
    second, _ = _simulate(argv, tmp_path / "b")
    a = pd.read_parquet(first / "bms_readings_sim.parquet")
    b = pd.read_parquet(second / "bms_readings_sim.parquet")
    assert a.equals(b)


def test_cli_and_pipeline_agree_on_the_run_start(argv, tmp_path):
    """`make iot-offline` and the individual CLIs must not silently disagree:
    the README quotes numbers from both."""
    import run_pipeline

    out, _ = _simulate(argv, tmp_path)
    cli_truth = json.loads((out / "truth.json").read_text(encoding="utf-8"))
    result = run_pipeline.run(
        start=pd.Timestamp(cli_truth["start"]).to_pydatetime(),
        duration_hours=2.0,
        interval_minutes=5,
        seed=cli_truth["seed"],
        faults=[],
        out_dir=tmp_path / "pipeline",
    )
    assert result.truth["start"] == cli_truth["start"]
    assert result.truth["interval_minutes"] == cli_truth["interval_minutes"]


def test_contract_cli_reports_both_rates(argv, tmp_path, capsys):
    """99.83% of all messages and 100% of valid messages answer different
    questions; printing only one of them invites a wrong reading."""
    out, _ = _simulate(argv, tmp_path)
    argv("--readings", str(out / "bms_readings_sim.parquet"), "--out", str(tmp_path / "split"))
    ingest_contract.main()
    printed = capsys.readouterr().out
    assert "of valid" in printed
    assert "of all" in printed
    assert "valid:" in printed


def test_contract_cli_rates_are_consistent_with_the_row_counts(argv, tmp_path, capsys):
    out, _ = _simulate(argv, tmp_path)
    argv("--readings", str(out / "bms_readings_sim.parquet"), "--out", str(tmp_path / "split"))
    ingest_contract.main()
    printed = capsys.readouterr().out
    messages = int(next(line for line in printed.splitlines() if line.startswith("messages:")).split()[-1])
    valid = int(next(line for line in printed.splitlines() if line.startswith("valid:")).split()[-1])
    accepted_line = next(line for line in printed.splitlines() if line.startswith("accepted:"))
    accepted = int(accepted_line.split()[1])
    dead = int(next(line for line in printed.splitlines() if line.startswith("dead-letter:")).split()[-1])
    assert accepted + dead == messages
    assert valid == messages - dead


def test_cli_writes_relative_to_the_given_out_dir(argv, tmp_path):
    """No CLI may write outside its --out; the repo's data/ is gitignored and a
    stray file elsewhere would be committed."""
    out, _ = _simulate(argv, tmp_path)
    assert sorted(p.name for p in out.iterdir()) == ["bms_readings_sim.parquet", "truth.json"]
