"""Metric registry: schema, coverage of dashboard KPIs, and the extraction rules.

Hand-checked fixtures first (the DAX and kpis.py cases), then the real repository.
"""

from __future__ import annotations

from pathlib import Path

import checks
import dashboards
import glossary as glossary_mod
import metrics
import yaml

BASE_METRIC: dict[str, object] = {
    "id": "sample_metric",
    "name": "Sample KPI",
    "kind": "metric",
    "status": "live",
    "definition": "A sample definition for tests.",
    "formula": "sum(x)",
    "grain": "space",
    "owner": "estates-analytics",
    "source_model": ["dim_space"],
    "caveats": ["Sample caveat."],
    "version": "1.0.0",
    "dashboards": ["p06"],
    "glossary_term": "nia",
    "classification": "internal",
}


def write_registry(tmp_path: Path, metrics_list: list[dict[str, object]], owners: list[str] | None = None) -> Path:
    path = tmp_path / "metrics.yml"
    payload = {
        "owners": [{"id": o, "role": "test"} for o in (owners or ["estates-analytics"])],
        "metrics": metrics_list,
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
    return path


# --------------------------------------------------------------------- DAX
def test_measure_names_from_fixture(dax_fixture: str) -> None:
    """Hand-checked: five measures, no DAX keywords, no comment fragments."""
    assert dashboards.measure_names(dax_fixture) == [
        "Total WOs",
        "PPM Completion %",
        "Remaining Life %",
        "Frequency %",
        "SLA Met %",
    ]


def test_measure_names_excludes_keywords_and_comments(dax_fixture: str) -> None:
    names = dashboards.measure_names(dax_fixture)
    assert "VAR TargetDays" not in names
    assert "RETURN" not in names
    assert "SWITCH" not in names
    assert "DIVIDE" not in names
    assert not any(n.startswith("Format") for n in names)
    assert not any("calculated column" in n for n in names)


def test_measure_names_single_line_and_multiline() -> None:
    dax = "One Line = SUM ( x )\nTwo Line =\n    SUM ( x )\nThree Line = SUM ( x )\n"
    assert dashboards.measure_names(dax) == ["One Line", "Two Line", "Three Line"]


def test_measure_names_are_deduplicated() -> None:
    assert dashboards.measure_names("A =\nB =\nA =\n") == ["A", "B"]


def test_kpi_function_names_ignores_private() -> None:
    source = "def public_one():\n    return 1\n\n\ndef _private():\n    return 2\n"
    assert dashboards.kpi_function_names(source) == ["public_one"]


def test_scan_projects_reads_both_sources(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    p07 = projects / "p07-demo"
    (p07 / "powerbi").mkdir(parents=True)
    (p07 / "src").mkdir(parents=True)
    (p07 / "powerbi" / "measures.dax").write_text("Cost = 1\n", encoding="utf-8")
    (p07 / "src" / "kpis.py").write_text("def mttr():\n    return 1\n", encoding="utf-8")
    (projects / "p06-empty" / "src").mkdir(parents=True)

    found = dashboards.scan_projects(projects, tmp_path, ("p06", "p07"))
    assert {(k.project, k.name) for k in found} == {("p07", "Cost"), ("p07", "mttr")}


def test_projects_with_handoff_reports_path(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    (projects / "p09-x" / "powerbi").mkdir(parents=True)
    (projects / "p09-x" / "powerbi" / "measures.dax").write_text("A =\n", encoding="utf-8")
    assert dashboards.projects_with_handoff(projects) == {"p09": "projects/p09-x/powerbi/measures.dax"}


MODEL_MD = (
    "# P10 Power BI model (synthetic)\n"
    "\n"
    "## Measures (DAX)\n"
    "\n"
    "```dax\n"
    "Total NIA = SUM(building_areas[nia_m2])\n"
    "Validation Blocking = COUNTROWS(FILTER(validation_report, validation_report[severity]=\"blocking\"))\n"
    "```\n"
    "\n"
    "```sql\n"
    "SELECT 1; -- this is not a measure\n"
    "```\n"
)


def test_model_md_measures_only_reads_dax_fences() -> None:
    assert dashboards.dax_blocks(MODEL_MD) != []
    assert dashboards.model_md_measures(MODEL_MD) == ["Total NIA", "Validation Blocking"]


def test_model_md_without_dax_fence_is_not_a_handoff(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "p10-x"
    (project / "powerbi").mkdir(parents=True)
    (project / "powerbi" / "model.md").write_text("# model\n\n| Table | Grain |\n|---|---|\n", encoding="utf-8")
    assert dashboards.handoff_files(project, tmp_path) == []


def test_model_md_handoff_is_scanned(tmp_path: Path) -> None:
    project = tmp_path / "projects" / "p10-x"
    (project / "powerbi").mkdir(parents=True)
    (project / "powerbi" / "model.md").write_text(MODEL_MD, encoding="utf-8")
    found = dashboards.scan_projects(tmp_path / "projects", tmp_path, ("p10",))
    assert {k.name for k in found} == {"Total NIA", "Validation Blocking"}
    assert all(k.source.endswith("powerbi/model.md") for k in found)


# ---------------------------------------------------------------- registry
def test_repository_registry_is_valid(registry) -> None:
    gloss = glossary_mod.load_glossary(checks.PROJECT_DIR / "glossary.yml")
    problems = metrics.validate(
        registry,
        gloss.ids,
        checks.known_consumers(),
        checks.owner_usage(
            checks.PROJECT_DIR / "glossary.yml",
            checks.PROJECT_DIR / "raci.yml",
            checks.PROJECT_DIR / "standards.yml",
        ),
    )
    assert problems == []


def test_repository_source_models_exist(registry) -> None:
    assert metrics.source_model_problems(registry, checks.DBT_MODELS_DIR) == []


def test_real_registry_covers_every_dashboard_kpi(registry) -> None:
    kpis, _ = checks.load_scan()
    assert metrics.coverage_problems(registry, kpis) == []
    assert len({k.name for k in kpis}) >= 40


def test_unregistered_kpi_is_reported(registry) -> None:
    kpis = [*checks.load_scan()[0], dashboards.DashboardKpi("Brand New KPI", "p06", "x.dax")]
    problems = metrics.coverage_problems(registry, kpis)
    assert any("Brand New KPI" in p and "no metrics.yml entry" in p for p in problems)


def test_registry_entry_without_consumer_is_reported(registry) -> None:
    kpis = [k for k in checks.load_scan()[0] if k.name != "NIA m2"]
    problems = metrics.coverage_problems(registry, kpis)
    assert any("nia_m2" in p and "no dashboard publishes it" in p for p in problems)


def test_planned_entries_may_have_no_consumer(registry) -> None:
    """The 'and vice versa' rule: an entry needs a consumer unless it is planned."""
    assert [m for m in registry.live if not m.dashboards] == []
    assert all(m.caveats for m in registry.planned)


def test_duplicate_name_is_reported(tmp_path: Path) -> None:
    second = {**BASE_METRIC, "id": "sample_metric_two", "name": "Sample KPI"}
    path = write_registry(tmp_path, [BASE_METRIC, second])
    problems = metrics.validate(metrics.load_registry(path), {"nia"}, {"p06"})
    assert any("duplicate name" in p for p in problems)


def test_unknown_consumer_is_reported(tmp_path: Path) -> None:
    path = write_registry(tmp_path, [{**BASE_METRIC, "dashboards": ["p99"]}])
    problems = metrics.validate(metrics.load_registry(path), {"nia"}, {"p06", "p07"})
    assert any("unknown consumer" in p for p in problems)


def test_missing_glossary_term_is_reported(tmp_path: Path) -> None:
    path = write_registry(tmp_path, [{**BASE_METRIC, "glossary_term": "not_a_term"}])
    problems = metrics.validate(metrics.load_registry(path), {"nia"}, {"p06"})
    assert any("glossary_term" in p for p in problems)


def test_metric_without_source_model_is_reported(tmp_path: Path) -> None:
    path = write_registry(tmp_path, [{**BASE_METRIC, "source_model": []}])
    problems = metrics.validate(metrics.load_registry(path), {"nia"}, {"p06"})
    assert any("source model" in p for p in problems)


def test_helper_may_have_no_source_model(tmp_path: Path) -> None:
    path = write_registry(tmp_path, [{**BASE_METRIC, "kind": "helper", "source_model": []}])
    assert metrics.validate(metrics.load_registry(path), {"nia"}, {"p06"}) == []


def test_live_entry_without_consumer_is_reported(tmp_path: Path) -> None:
    path = write_registry(tmp_path, [{**BASE_METRIC, "dashboards": []}])
    problems = metrics.validate(metrics.load_registry(path), {"nia"}, {"p06"})
    assert any("must name at least one consumer" in p for p in problems)


def test_bad_source_model_is_reported(tmp_path: Path) -> None:
    path = write_registry(tmp_path, [{**BASE_METRIC, "source_model": ["not_a_model"]}])
    problems = metrics.source_model_problems(metrics.load_registry(path), checks.DBT_MODELS_DIR)
    assert any("not_a_model" in p for p in problems)


def test_external_source_prefixes_are_accepted(tmp_path: Path) -> None:
    path = write_registry(tmp_path, [{**BASE_METRIC, "source_model": ["file:x.csv", "dq:y.parquet"]}])
    assert metrics.source_model_problems(metrics.load_registry(path), checks.DBT_MODELS_DIR) == []


def test_dbt_model_names_from_real_project() -> None:
    names = metrics.dbt_model_names(checks.DBT_MODELS_DIR)
    assert {"mart_space_utilisation", "fct_work_order", "dim_space"} <= names


def test_scan_scope_covers_every_handoff(registry) -> None:
    """A new dashboard cannot escape registry coverage without an explicit decision."""
    _, handoffs = checks.load_scan()
    unscanned = set(handoffs) - set(checks.SCAN_SCOPE)
    assert unscanned <= set(checks.SCAN_EXCLUSIONS), f"unscanned hand-off projects: {sorted(unscanned)}"
    assert all(reason.strip() for reason in checks.SCAN_EXCLUSIONS.values())
