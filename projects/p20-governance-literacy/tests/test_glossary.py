"""Glossary: schema, required terms, and 100% coverage of dashboard KPIs."""

from __future__ import annotations

import checks
import dashboards
import glossary as glossary_mod
import pytest
import yaml


def test_glossary_owners_exist(registry, glossary) -> None:
    problems = glossary_mod.validate(glossary, set(registry.owner_ids))
    assert problems == []


def test_glossary_covers_every_dashboard_kpi(glossary) -> None:
    kpis, _ = checks.load_scan()
    assert glossary_mod.coverage_problems(glossary, kpis) == []


def test_undefined_dashboard_kpi_is_reported(glossary) -> None:
    kpis = [*checks.load_scan()[0], dashboards.DashboardKpi("Mystery KPI", "p08", "x.dax")]
    problems = glossary_mod.coverage_problems(glossary, kpis)
    assert any("Mystery KPI" in p and "no glossary definition" in p for p in problems)


def test_alias_for_nothing_published_is_reported(glossary) -> None:
    kpis = [k for k in checks.load_scan()[0] if k.name != "NIA m2"]
    problems = glossary_mod.coverage_problems(glossary, kpis)
    assert any("NIA m2" in p for p in problems)


def test_spec_required_terms_present(glossary) -> None:
    """The terms the spec names by name must exist."""
    for term in (
        "gia",
        "nia",
        "fte",
        "ppm",
        "reactive",
        "mttr",
        "utilisation",
        "scope_1",
        "scope_2",
        "baseload",
        "cobie",
        "air",
    ):
        assert term in glossary.ids, f"spec-required term missing: {term}"


def test_missing_required_term_is_reported(tmp_path) -> None:
    payload = yaml.safe_load(checks.PROJECT_DIR.joinpath("glossary.yml").read_text(encoding="utf-8"))
    payload["required_terms"] = ["not_a_term"]
    path = tmp_path / "glossary.yml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    problems = glossary_mod.validate(glossary_mod.load_glossary(path), {"estates-analytics"})
    assert any("required term" in p for p in problems)


def test_bad_refresh_value_is_reported(tmp_path) -> None:
    payload = yaml.safe_load(checks.PROJECT_DIR.joinpath("glossary.yml").read_text(encoding="utf-8"))
    payload["terms"][0]["refresh"] = "hourly-ish"
    path = tmp_path / "glossary.yml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    problems = glossary_mod.validate(glossary_mod.load_glossary(path), {"estates-analytics"})
    assert any("refresh" in p for p in problems)


def test_alias_to_unknown_term_is_reported(tmp_path) -> None:
    payload = yaml.safe_load(checks.PROJECT_DIR.joinpath("glossary.yml").read_text(encoding="utf-8"))
    payload["kpi_aliases"]["Made Up KPI"] = "no_such_term"
    path = tmp_path / "glossary.yml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    problems = glossary_mod.validate(glossary_mod.load_glossary(path), {"estates-analytics"})
    assert any("no_such_term" in p for p in problems)


# ----------------------------------------------------------------- DQ join
def test_load_dq_scores_reads_latest_dataset_rows(tmp_path) -> None:
    csv = tmp_path / "dq_scores.csv"
    csv.write_text(
        "run_id,grain,dataset,key,score,n_checks\n"
        "r1,dataset,spaces,,90.0,3\n"
        "r2,dataset,spaces,,99.0,5\n"
        "r2,dimension,spaces,completeness,80.0,2\n",
        encoding="utf-8",
    )
    assert glossary_mod.load_dq_scores(csv) == {"spaces": 99.0}


def test_load_dq_scores_missing_file(tmp_path) -> None:
    assert glossary_mod.load_dq_scores(tmp_path / "absent.csv") == {}


def test_dq_score_for_concept_and_missing_run(glossary) -> None:
    nia = glossary.by_id()["nia"]
    assert "not measured" in glossary_mod.dq_score_for(nia, {})
    assert "99.0/100 (spaces" in glossary_mod.dq_score_for(nia, {"spaces": 99.0})
    cde = glossary.by_id()["cde"]
    assert "not dataset-scored" in glossary_mod.dq_score_for(cde, {"spaces": 99.0})


def test_dq_score_reports_unknown_dataset(glossary) -> None:
    term = glossary_mod.Term("x", "X", "d", "estates-analytics", "s", "daily", "not_a_dataset", "internal", "")
    assert "not scored" in glossary_mod.dq_score_for(term, {"spaces": 99.0})


def test_real_dq_scores_cover_known_datasets() -> None:
    scores = glossary_mod.load_dq_scores(checks.DQ_SCORES_CSV)
    if scores:
        assert "spaces" in scores
        assert all(0.0 <= value <= 100.0 for value in scores.values())


@pytest.mark.parametrize("term_id", ["nia", "gia", "ppm", "mttr"])
def test_terms_with_dataset_have_one(glossary, term_id: str) -> None:
    term = glossary.by_id()[term_id]
    assert term.dataset in {
        "",
        "spaces",
        "assets",
        "work_orders",
        "timetable",
        "sensors",
        "meters_a",
        "meters_b",
        "inspections",
        "bms",
    }
