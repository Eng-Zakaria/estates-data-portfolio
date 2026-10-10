"""The gate runner and the CLI: the wiring CI actually runs."""

from __future__ import annotations

import shutil
from pathlib import Path

import checks
import cli
import config
import pytest
import yaml
from typer.testing import CliRunner

runner = CliRunner()


def make_project(tmp_path: Path, drop_alias: str | None = None) -> Path:
    """A minimal project tree: the four YAML sources, an empty docs directory."""
    project = tmp_path / "p20-copy"
    project.mkdir()
    for name in ("metrics.yml", "glossary.yml", "raci.yml", "standards.yml"):
        shutil.copy(config.PROJECT_DIR / name, project / name)
    (project / "docs").mkdir()
    if drop_alias:
        payload = yaml.safe_load((project / "glossary.yml").read_text(encoding="utf-8"))
        payload["kpi_aliases"].pop(drop_alias)
        (project / "glossary.yml").write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return project


# ------------------------------------------------------------------- gates
def test_run_all_passes_on_the_real_project() -> None:
    run = checks.run_all()
    assert run.ok, [str(g) for g in run.failures()]
    assert run.kpi_count >= 40
    assert run.generated_written == [], "check must not rewrite pages"
    assert [g.name for g in run.gates] == [
        "metric registry schema",
        "glossary schema",
        "KPI scan scope",
        "dashboard KPI coverage (registry + glossary)",
        "generated pages not stale",
        "in-site links",
        "literacy page readability",
    ]


def test_undefined_kpi_fails_the_coverage_gate(tmp_path: Path) -> None:
    run = checks.run_all(make_project(tmp_path, drop_alias="NIA m2"))
    assert not run.ok
    failing = {g.name: g.problems for g in run.failures()}
    assert "dashboard KPI coverage (registry + glossary)" in failing
    assert any("NIA m2" in p for p in failing["dashboard KPI coverage (registry + glossary)"])


def test_missing_docs_directory_is_reported_not_passed(tmp_path: Path) -> None:
    project = make_project(tmp_path)
    shutil.rmtree(project / "docs")
    run = checks.run_all(project)
    names = {g.name: g for g in run.gates}
    assert names["in-site links"].skipped
    assert not run.ok
    assert names["literacy page readability"].problems


def test_write_then_check_is_idempotent() -> None:
    run = checks.run_all(write=True)
    assert run.ok
    assert checks.run_all().ok


def test_render_pages_honours_dq_score_absence(tmp_path: Path) -> None:
    pages = checks.render_pages(dq_scores_csv=tmp_path / "absent.csv")
    assert "No data quality results" in pages["generated/dq-scores.md"]
    assert "not measured in this checkout" in pages["generated/glossary.md"]


def test_known_consumers_include_projects_and_platform() -> None:
    consumers = checks.known_consumers()
    assert {"p06", "p07", "p08", "p09", "p11", "p03"} <= consumers


def test_load_scan_returns_kpis_and_handoffs() -> None:
    kpis, handoffs = checks.load_scan()
    assert any(k.name == "Utilisation %" for k in kpis)
    assert "p07" in handoffs


# --------------------------------------------------------------------- CLI
def test_cli_check_exits_zero() -> None:
    result = runner.invoke(cli.app, ["check"])
    assert result.exit_code == 0, result.output
    assert "P20 checks passed" in result.output
    assert "FAIL" not in result.output


def test_cli_build_is_idempotent() -> None:
    result = runner.invoke(cli.app, ["build"])
    assert result.exit_code == 0, result.output
    assert "0 of 7 generated pages updated" in result.output


def test_cli_readability_lists_every_page() -> None:
    result = runner.invoke(cli.app, ["readability"])
    assert result.exit_code == 0
    for page in config.LITERACY_PAGES:
        assert page in result.output
    assert "target 50" not in result.output  # the target line is in `check`
    assert "min" in result.output


def test_cli_coverage_reports_completion() -> None:
    result = runner.invoke(cli.app, ["coverage"])
    assert result.exit_code == 0, result.output
    assert "coverage is complete in both directions" in result.output


def test_cli_links_reports_counts() -> None:
    result = runner.invoke(cli.app, ["links"])
    assert result.exit_code == 0, result.output
    assert "in-site links checked" in result.output


def test_cli_list_generated() -> None:
    result = runner.invoke(cli.app, ["list-generated"])
    assert result.exit_code == 0
    assert result.output.strip().count("docs/generated/") == len(config.GENERATED_PAGES)


@pytest.mark.parametrize("command", [["build"], ["check"], ["readability"], ["coverage"], ["links"]])
def test_cli_commands_have_help(command: list[str]) -> None:
    result = runner.invoke(cli.app, [*command, "--help"])
    assert result.exit_code == 0
    assert "Usage" in result.output
