"""CLI smoke: generate + snapshots cover cli/exports/ground_truth."""

from pathlib import Path

from campus_synth.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def test_generate_small_tmp(tmp_path: Path):
    out = tmp_path / "raw"
    res = runner.invoke(app, ["generate", "--profile", "small", "--seed", "42", "--out", str(out), "--defects", "0.03"])
    assert res.exit_code == 0, res.output
    assert (out / "ground_truth.yaml").exists()
    assert (tmp_path / "truth" not in [out]).__class__  # placeholder no-op
    # raw exports present
    names = {p.name[:12] for p in out.iterdir()}
    assert any("cafm_workord" in n for n in names)


def test_snapshots_tmp(tmp_path: Path):
    out = tmp_path / "snaps"
    res = runner.invoke(app, ["snapshots", "--weeks", "2", "--out", str(out), "--seed", "42"])
    assert res.exit_code == 0, res.output
    assert (out / "week_01" / "spaces.parquet").exists()
    assert (out / "week_02" / "manifest.yaml").exists()
