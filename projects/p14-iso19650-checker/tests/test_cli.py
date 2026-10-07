"""CLI behaviour: report formats, exit codes and the CI gate."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from cli import app
from conftest import UK_CONVENTION, VARIANT_CONVENTION, write
from typer.testing import CliRunner

runner = CliRunner()


def outdir(root: Path) -> Path:
    """Report artefacts must live outside the checked tree, or they show up in the next run."""
    outside = root.parent / f"{root.name}_reports"
    outside.mkdir(exist_ok=True)
    return outside


@pytest.fixture
def tree(tmp_path):
    """A small mixed tree: one compliant container, one broken, one lower case."""
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0002-S4-P01.01.txt")  # S4 invalid in WIP
    write(tmp_path, "Shared/PRJ01-ENGG-ZZ-01-DR-A-0001-S1-P01.txt")
    write(tmp_path, "Shared/prj01-engg-zz-01-dr-a-0002-s1-p01.txt")  # fixable by rename
    return tmp_path


def run(folder: Path, *args: str):
    return runner.invoke(app, ["check", str(folder), "--config", str(UK_CONVENTION), *args])


def test_text_report_and_exit_code_on_errors(tree, tmp_path):
    result = run(tree, "--out", str(outdir(tmp_path)))
    assert result.exit_code == 1
    assert "status_container_mismatch" in result.output
    assert "Compliance:" in result.output
    assert (outdir(tmp_path) / "container_register.csv").exists()
    assert (outdir(tmp_path) / "compliance_summary.csv").exists()
    assert (outdir(tmp_path) / "suggested_renames.csv").exists()


def test_clean_tree_exits_zero(tmp_path):
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    result = run(tmp_path, "--out", str(outdir(tmp_path)))
    assert result.exit_code == 0
    assert "0 errors" in result.output


def test_fail_on_none_reports_but_passes(tree, tmp_path):
    result = run(tree, "--fail-on", "none", "--out", str(outdir(tmp_path)))
    assert result.exit_code == 0
    assert "status_container_mismatch" in result.output


def test_fail_on_warning_gates_on_warnings(tree, tmp_path):
    result = run(tree, "--fail-on", "warning", "--out", str(outdir(tmp_path)))
    assert result.exit_code == 1


def test_json_report_shape(tree, tmp_path):
    out = outdir(tmp_path)
    assert run(tree, "--format", "json", "--quiet", "--out", str(out)).exit_code == 1
    payload = json.loads((out / "issues.json").read_text(encoding="utf-8"))
    assert payload["convention"] == "uk_national_annex"
    assert payload["errors"] >= 1
    assert {i["rule_id"] for i in payload["issues"]} >= {"status_container_mismatch"}
    assert payload["summary"][0]["dimension"] == "overall"
    assert payload["suggested_renames"] == []  # not requested, so not offered


def test_html_report_renders(tree, tmp_path):
    out = outdir(tmp_path)
    assert run(tree, "--format", "html", "--quiet", "--out", str(out)).exit_code == 1
    html = (out / "report.html").read_text(encoding="utf-8")
    assert "<table>" in html and "status_container_mismatch" in html
    assert "uk_national_annex" in html
    assert "Synthetic demonstration data" in html
    assert "cdbb.cam.ac.uk" in html  # provenance is shown in the report footer


def test_junit_report_is_ci_usable(tree, tmp_path):
    out = outdir(tmp_path)
    assert run(tree, "--format", "junit", "--quiet", "--out", str(out)).exit_code == 1
    root = ET.parse(out / "junit.xml").getroot()
    suite = root.find("testsuite")
    assert suite is not None
    assert int(suite.get("failures")) >= 1
    names = {case.get("name") for case in suite.findall("testcase")}
    assert any(name.startswith("status_container_mismatch") for name in names)


def test_junit_report_of_a_clean_run_is_green(tmp_path):
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    out = outdir(tmp_path)
    assert run(tmp_path, "--format", "junit", "--quiet", "--out", str(out)).exit_code == 0
    suite = ET.parse(out / "junit.xml").getroot().find("testsuite")
    assert int(suite.get("failures")) == 0
    assert suite.find("testcase") is not None  # a visible pass, not an empty report


def test_suggest_lists_renames_without_touching_disk(tree, tmp_path):
    before = sorted(p.name for p in tree.rglob("*") if p.is_file())
    result = run(tree, "--suggest", "--out", str(outdir(tmp_path)))
    assert result.exit_code == 1
    assert "Suggested renames" in result.output
    assert sorted(p.name for p in tree.rglob("*") if p.is_file()) == before
    renames = (outdir(tmp_path) / "suggested_renames.csv").read_text(encoding="utf-8")
    assert "prj01-engg" in renames and "PRJ01-ENGG" in renames


def test_register_option_reports_orphans(tree, tmp_path):
    register = tmp_path.parent / f"{tmp_path.name}_reg.csv"
    register.write_text("path\nWIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt\n", encoding="utf-8")
    result = run(tree, "--register", str(register), "--format", "json", "--quiet", "--out", str(outdir(tmp_path)))
    payload = json.loads((outdir(tmp_path) / "issues.json").read_text(encoding="utf-8"))
    orphans = [i["path"] for i in payload["issues"] if i["rule_id"] == "orphan_file"]
    assert len(orphans) == 3
    assert result.exit_code == 1


def test_unknown_format_is_rejected(tree, tmp_path):
    result = run(tree, "--format", "pdf", "--out", str(outdir(tmp_path)))
    assert result.exit_code != 0
    assert "--format must be" in result.output


def test_apply_and_rollback_through_the_cli(tree, tmp_path):
    log = outdir(tmp_path) / "rename_log.csv"
    dry = runner.invoke(app, ["apply", str(tree), "--config", str(UK_CONVENTION), "--log", str(log)])
    assert "DRY RUN" in dry.output
    assert (tree / "Shared" / "prj01-engg-zz-01-dr-a-0002-s1-p01.txt").exists()

    applied = runner.invoke(app, ["apply", str(tree), "--config", str(UK_CONVENTION), "--log", str(log), "--apply"])
    assert "APPLIED" in applied.output
    assert (tree / "Shared" / "PRJ01-ENGG-ZZ-01-DR-A-0002-S1-P01.txt").exists()

    undone = runner.invoke(app, ["rollback", str(tree), "--log", str(log)])
    assert "Rolled back 1" in undone.output
    assert (tree / "Shared" / "prj01-engg-zz-01-dr-a-0002-s1-p01.txt").exists()


def test_check_with_the_second_convention(tmp_path):
    """Same tree, two conventions: compliant under the estates variant, broken under the Annex."""
    write(tmp_path, "WIP/PRJ01_ESTM_ZZ_01_DR_A_PR1_0001_WIP.csv")
    ok = runner.invoke(
        app,
        [
            "check",
            str(tmp_path),
            "--config",
            str(VARIANT_CONVENTION),
            "--quiet",
            "--out",
            str(outdir(tmp_path)),
        ],
    )
    assert ok.exit_code == 0
    bad = runner.invoke(
        app,
        [
            "check",
            str(tmp_path),
            "--config",
            str(UK_CONVENTION),
            "--quiet",
            "--out",
            str(outdir(tmp_path)),
        ],
    )
    assert bad.exit_code == 1
