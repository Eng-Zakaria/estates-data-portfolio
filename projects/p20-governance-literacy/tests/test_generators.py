"""Generators: dbt metadata parsing, page rendering, determinism and staleness."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import checks
import dbt_meta
import generate


# ------------------------------------------------------------- dbt parsing
def test_models_and_columns_from_fixture(dbt_fixture_tree: Path) -> None:
    meta = dbt_meta.load(dbt_fixture_tree)
    assert meta.source == "yaml+sql"
    names = meta.by_name
    assert {"stg_meter__hh", "mart_energy"} <= set(names)
    mart = names["mart_energy"]
    assert mart.layer == "marts"
    assert mart.materialization == "table"
    assert [c.name for c in mart.columns] == ["building_id", "kwh"]
    assert mart.columns[0].tests == ["not_null", "unique"]


def test_ref_and_source_edges_from_fixture(dbt_fixture_tree: Path) -> None:
    meta = dbt_meta.load(dbt_fixture_tree)
    assert "stg_meter__hh" in meta.by_name["mart_energy"].depends_on
    assert "meter.hh_a" in meta.by_name["stg_meter__hh"].depends_on


def test_exposures_from_fixture(dbt_fixture_tree: Path) -> None:
    meta = dbt_meta.load(dbt_fixture_tree)
    assert [e.name for e in meta.exposures] == ["energy_dashboard"]
    assert meta.exposures[0].depends_on == ["mart_energy"]
    assert ("mart_energy", "energy_dashboard") in meta.edges


def test_edges_only_include_known_nodes(dbt_fixture_tree: Path) -> None:
    """dim_building is referenced by SQL but has no YAML, so it is not a node."""
    meta = dbt_meta.load(dbt_fixture_tree)
    known = set(meta.by_name) | {e.name for e in meta.exposures}
    assert "dim_building" not in known
    assert all(child in known for _, child in meta.edges)
    assert all(parent in known for parent, _ in meta.edges)


def test_manifest_path_is_preferred(dbt_fixture_tree: Path, tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "nodes": {
                    "model.p.mart_energy": {
                        "name": "mart_energy",
                        "resource_type": "model",
                        "path": "marts/mart_energy.sql",
                        "description": "From the manifest.",
                        "config": {"materialized": "table"},
                        "columns": {"building_id": {"type": "VARCHAR", "description": "Building"}},
                        "depends_on": {"nodes": ["model.p.stg_meter__hh"]},
                    }
                },
                "exposures": {
                    "exposure.p.energy_dashboard": {
                        "name": "energy_dashboard",
                        "description": "Dash",
                        "type": "dashboard",
                        "owner": {"name": "estates-analytics"},
                        "depends_on": {"nodes": ["model.p.mart_energy"]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    meta = dbt_meta.load(dbt_fixture_tree, manifest)
    assert meta.source == "manifest"
    assert meta.manifest_found
    assert meta.by_name["mart_energy"].description == "From the manifest."
    assert meta.by_name["mart_energy"].columns[0].data_type == "VARCHAR"
    assert [e.name for e in meta.exposures] == ["energy_dashboard"]


def test_missing_models_dir_degrades(tmp_path: Path) -> None:
    meta = dbt_meta.load(tmp_path / "absent")
    assert meta.models == [] and meta.exposures == []


def test_real_dbt_project_reads() -> None:
    meta = dbt_meta.load(checks.DBT_MODELS_DIR, checks.DBT_TARGET_MANIFEST)
    assert len(meta.models) >= 40
    assert {m.layer for m in meta.models} >= {"staging", "marts"}
    assert any(parent == "mart_space_utilisation" for parent, _ in meta.edges)


# --------------------------------------------------------------- rendering
def test_cell_escapes_pipes_and_whitespace() -> None:
    assert generate.cell("a | b") == "a / b"
    assert generate.cell("  lots   of\nspace ") == "lots of space"
    assert generate.cell("") == "-"


def test_table_renders_header_and_separator() -> None:
    out = generate.table(["A", "B"], [["1", "2"]])
    assert out.splitlines()[0] == "| A | B |"
    assert out.splitlines()[1] == "|---|---|"
    assert out.splitlines()[2] == "| 1 | 2 |"


def test_dictionary_page_contains_models_and_columns(dbt_fixture_tree: Path) -> None:
    page = generate.render_dictionary(dbt_meta.load(dbt_fixture_tree))
    assert "### `mart_energy`" in page
    assert "building_id" in page
    assert "Marts" in page
    assert "GENERATED FILE" in page


def test_lineage_page_has_mermaid_and_exposures(dbt_fixture_tree: Path) -> None:
    page = generate.render_lineage(dbt_meta.load(dbt_fixture_tree))
    assert "```mermaid" in page
    assert "flowchart LR" in page
    assert "mart_energy --> energy_dashboard" in page


def test_dq_scores_page_without_data_is_honest(tmp_path: Path) -> None:
    page = generate.render_dq_scores(tmp_path / "absent.csv", tmp_path / "a.csv", tmp_path / "b.csv")
    assert "No data quality results in this checkout" in page
    assert "make dq-check" in page
    assert "| Dataset |" not in page


def test_dq_scores_page_with_data_uses_latest_run(tmp_path: Path) -> None:
    scores = tmp_path / "dq_scores.csv"
    with scores.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["run_id", "grain", "dataset", "key", "score", "n_checks"])
        writer.writerow(["r1", "dataset", "spaces", "", "90.0", "3"])
        writer.writerow(["r2", "dataset", "spaces", "", "99.5", "5"])
        writer.writerow(["r2", "dimension", "spaces", "completeness", "88.0", "2"])
        writer.writerow(["r2", "dataset", "assets", "", "100.0", "4"])
    results = tmp_path / "dq_results.csv"
    results.write_text(
        "run_id,dataset,check_id,dimension,severity,engine,rows_checked,rows_failed,pass_rate,threshold,status\n"
        "r2,spaces,spaces_room_not_null,completeness,error,sql,100,1,0.99,100.0,fail\n"
        "r2,assets,assets_install_not_future,validity,error,sql,50,0,1.0,100.0,pass\n",
        encoding="utf-8",
    )
    alerts = tmp_path / "dq_alerts.csv"
    alerts.write_text("run_id,alert_kind,dataset,detail\nr2,error_fail,spaces,check failed\n", encoding="utf-8")

    page = generate.render_dq_scores(scores, results, alerts)
    assert "Run `r2`" in page
    assert "| spaces | 99.5 | 5 |" in page
    assert "spaces_room_not_null" in page
    assert "error_fail" in page
    assert "Run `r1`" not in page


def test_glossary_page_shows_dq_score(glossary) -> None:
    page = generate.render_glossary(glossary, {"spaces": 99.5})
    assert "99.5/100 (spaces, run output)" in page
    assert "not measured in this checkout" in generate.render_glossary(glossary, {})


def test_metric_registry_page_lists_entries(registry, glossary) -> None:
    page = generate.render_metric_registry(registry, glossary)
    assert "## Utilisation %" in page
    assert "**Formula**" in page
    assert "**Caveats**" in page


def test_raci_and_standards_pages_render() -> None:
    import yaml

    raci = yaml.safe_load(checks.PROJECT_DIR.joinpath("raci.yml").read_text(encoding="utf-8"))
    standards = yaml.safe_load(checks.PROJECT_DIR.joinpath("standards.yml").read_text(encoding="utf-8"))
    raci_page = generate.render_raci(raci)
    assert "Space and estate planning" in raci_page
    assert "Decision rights that apply everywhere" in raci_page
    standards_page = generate.render_standards(standards["standards"])
    assert "not-obtained" in standards_page
    assert "ISO 19650" in standards_page


# -------------------------------------------------------- write and staleness
def test_write_pages_is_deterministic(tmp_path: Path) -> None:
    pages = checks.render_pages()
    first = checks.write_pages(pages, tmp_path)
    second = checks.write_pages(pages, tmp_path)
    assert len(first) == len(pages)
    assert second == []


def test_stale_problems_detects_missing_and_changed(tmp_path: Path) -> None:
    pages = {"generated/x.md": "hello\n", "generated/y.md": "world\n"}
    expected = ("generated/x.md", "generated/y.md")
    problems = checks.stale_problems(pages, tmp_path, expected)
    assert sorted(problems) == [
        "generated/x.md: missing (run `make p20-build`)",
        "generated/y.md: missing (run `make p20-build`)",
    ]
    (tmp_path / "generated").mkdir(parents=True)
    (tmp_path / "generated" / "x.md").write_text("hello\n", encoding="utf-8")
    (tmp_path / "generated" / "y.md").write_text("different\n", encoding="utf-8")
    assert checks.stale_problems(pages, tmp_path, expected) == ["generated/y.md: stale (run `make p20-build`)"]


def test_stale_problems_flags_unrendered_page(tmp_path: Path) -> None:
    problems = checks.stale_problems({}, tmp_path)
    assert problems == [f"{rel}: no renderer produced this page" for rel in checks.GENERATED_PAGES]


def test_render_pages_covers_every_declared_generated_page() -> None:
    assert set(checks.render_pages()) == set(checks.GENERATED_PAGES)


def test_repository_pages_are_not_stale() -> None:
    pages = checks.render_pages()
    assert checks.stale_problems(pages, checks.PROJECT_DIR / "docs") == []


def test_rendering_is_stable_across_runs() -> None:
    """Same inputs, same bytes: no timestamps, no dict ordering surprises."""
    assert checks.render_pages() == checks.render_pages()
