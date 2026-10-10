"""One place that runs every P20 gate, so CI and the Makefile agree.

The gates are:

1. registry schema and cross-references (``metrics.yml``);
2. registry coverage of dashboard KPIs, both directions;
3. glossary schema, required terms, and full coverage of dashboard KPIs;
4. generated pages are not stale (regenerate in memory, diff against disk);
5. in-site links and anchors resolve;
6. literacy pages meet the readability target, and every page is measured.

A gate that cannot run (no dbt project, no DQ output in the checkout) reports
itself as skipped with the reason. It never passes silently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import dashboards
import dbt_meta
import generate
import glossary as glossary_mod
import links as links_mod
import metrics as metrics_mod
import readability as readability_mod
import yaml
from config import (
    DBT_MODELS_DIR,
    DQ_ALERTS_CSV,
    DQ_RESULTS_CSV,
    DQ_SCORES_CSV,
    GENERATED_PAGES,
    GLOSSARY_YML,
    LITERACY_PAGES,
    METRICS_YML,
    PLATFORM_CONSUMERS,
    PROJECT_DIR,
    PROJECTS_DIR,
    RACI_YML,
    READABILITY_TARGET,
    REPO_ROOT,
    SCAN_EXCLUSIONS,
    SCAN_SCOPE,
    STANDARDS_YML,
)

DBT_TARGET_MANIFEST = REPO_ROOT / "platform" / "dbt" / "target" / "manifest.json"


@dataclass
class GateResult:
    name: str
    ok: bool
    skipped: bool = False
    problems: list[str] = field(default_factory=list)
    detail: str = ""

    def __str__(self) -> str:
        if self.skipped:
            return f"SKIP {self.name}: {self.detail}"
        status = "PASS" if self.ok else "FAIL"
        lines = [f"{status} {self.name}" + (f" - {self.detail}" if self.detail else "")]
        lines.extend(f"    - {p}" for p in self.problems)
        return "\n".join(lines)


@dataclass
class CheckRun:
    gates: list[GateResult]
    kpi_count: int
    readability: list[readability_mod.ReadabilityScore]
    readability_summary: dict[str, float | int | None]
    generated_written: list[str]

    @property
    def ok(self) -> bool:
        return all(g.ok or g.skipped for g in self.gates)

    def failures(self) -> list[GateResult]:
        return [g for g in self.gates if not g.ok and not g.skipped]


def known_consumers() -> set[str]:
    """Consumer ids a metric may point at: scanned projects plus platform ones."""
    ids = set(PLATFORM_CONSUMERS)
    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if project_dir.is_dir():
            ids.add(project_dir.name.split("-", 1)[0])
    return ids


def load_scan() -> tuple[list[dashboards.DashboardKpi], dict[str, str]]:
    kpis = dashboards.scan_projects(PROJECTS_DIR, REPO_ROOT, SCAN_SCOPE)
    handoffs = dashboards.projects_with_handoff(PROJECTS_DIR)
    return kpis, handoffs


def render_pages(
    *,
    dbt_models_dir: Path = DBT_MODELS_DIR,
    dq_scores_csv: Path = DQ_SCORES_CSV,
    dq_results_csv: Path = DQ_RESULTS_CSV,
    dq_alerts_csv: Path = DQ_ALERTS_CSV,
    metrics_yml: Path = METRICS_YML,
    glossary_yml: Path = GLOSSARY_YML,
    raci_yml: Path = RACI_YML,
    standards_yml: Path = STANDARDS_YML,
    manifest: Path = DBT_TARGET_MANIFEST,
) -> dict[str, str]:
    """Render every generated page. Keys are paths relative to ``docs/``."""
    meta = dbt_meta.load(dbt_models_dir, manifest)
    registry = metrics_mod.load_registry(metrics_yml)
    gloss = glossary_mod.load_glossary(glossary_yml)
    scores = glossary_mod.load_dq_scores(dq_scores_csv)
    raci = yaml.safe_load(raci_yml.read_text(encoding="utf-8"))
    standards = yaml.safe_load(standards_yml.read_text(encoding="utf-8"))

    return {
        "generated/data-dictionary.md": generate.render_dictionary(meta),
        "generated/lineage.md": generate.render_lineage(meta),
        "generated/dq-scores.md": generate.render_dq_scores(dq_scores_csv, dq_results_csv, dq_alerts_csv),
        "generated/glossary.md": generate.render_glossary(gloss, scores),
        "generated/metric-registry.md": generate.render_metric_registry(registry, gloss),
        "generated/standards-register.md": generate.render_standards(standards["standards"]),
        "generated/raci.md": generate.render_raci(raci),
    }


def write_pages(pages: dict[str, str], docs_dir: Path) -> list[str]:
    written: list[str] = []
    for rel, text in pages.items():
        target = docs_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or target.read_text(encoding="utf-8") != text:
            target.write_text(text, encoding="utf-8")
            written.append(rel)
    return written


def stale_problems(pages: dict[str, str], docs_dir: Path, expected: tuple[str, ...] | None = None) -> list[str]:
    """Compare freshly rendered pages against what is committed.

    ``expected`` defaults to the declared generated pages; tests pass a smaller
    list to exercise the logic without touching the whole site.
    """
    problems: list[str] = []
    for rel in expected or GENERATED_PAGES:
        target = docs_dir / rel
        if rel not in pages:
            problems.append(f"{rel}: no renderer produced this page")
            continue
        if not target.is_file():
            problems.append(f"{rel}: missing (run `make p20-build`)")
        elif target.read_text(encoding="utf-8") != pages[rel]:
            problems.append(f"{rel}: stale (run `make p20-build`)")
    return problems


def owner_usage(glossary_yml: Path, raci_yml: Path, standards_yml: Path) -> set[str]:
    """Owner ids that carry glossary, RACI or standards entries."""
    gloss = glossary_mod.load_glossary(glossary_yml)
    raci = yaml.safe_load(raci_yml.read_text(encoding="utf-8"))
    standards = yaml.safe_load(standards_yml.read_text(encoding="utf-8"))
    owners = {t.owner for t in gloss.terms}
    for domain in raci["domains"]:
        owners.add(str(domain["accountable"]))
    owners.update(str(r)["owner"] for r in raci["roles"] if isinstance(r, dict) and "owner" in r)
    owners.update(str(s["owner"]) for s in standards["standards"])
    return owners


def _gate_metrics(
    registry: metrics_mod.Registry,
    gloss: glossary_mod.Glossary,
    project_dir: Path,
) -> GateResult:
    problems = metrics_mod.validate(
        registry,
        gloss.ids,
        known_consumers(),
        owner_usage(
            project_dir / GLOSSARY_YML.name,
            project_dir / RACI_YML.name,
            project_dir / STANDARDS_YML.name,
        ),
    )
    problems += metrics_mod.source_model_problems(registry, DBT_MODELS_DIR)
    return GateResult(
        name="metric registry schema",
        ok=not problems,
        problems=problems,
        detail=f"{len(registry.metrics)} entries, {len(registry.owner_ids)} owners",
    )


def _gate_coverage(
    registry: metrics_mod.Registry, kpis: list[dashboards.DashboardKpi], gloss: glossary_mod.Glossary
) -> GateResult:
    problems = metrics_mod.coverage_problems(registry, kpis)
    problems += glossary_mod.coverage_problems(gloss, kpis)
    return GateResult(
        name="dashboard KPI coverage (registry + glossary)",
        ok=not problems,
        problems=problems,
        detail=f"{len({k.name for k in kpis})} dashboard KPI names checked both ways",
    )


def _gate_scan_scope(handoffs: dict[str, str]) -> GateResult:
    unscanned = sorted(set(handoffs) - set(SCAN_SCOPE))
    problems = [
        f"project {pid} ships {handoffs[pid]} but is neither in SCAN_SCOPE nor SCAN_EXCLUSIONS"
        for pid in unscanned
        if pid not in SCAN_EXCLUSIONS
    ]
    return GateResult(
        name="KPI scan scope",
        ok=not problems,
        problems=problems,
        detail=f"scanned {sorted(SCAN_SCOPE)}, excluded {sorted(SCAN_EXCLUSIONS)}",
    )


def _gate_glossary(gloss: glossary_mod.Glossary, registry: metrics_mod.Registry) -> GateResult:
    problems = glossary_mod.validate(gloss, set(registry.owner_ids))
    return GateResult(
        name="glossary schema",
        ok=not problems,
        problems=problems,
        detail=f"{len(gloss.terms)} terms, {len(gloss.required_terms)} required by the spec",
    )


def _gate_stale(pages: dict[str, str], docs_dir: Path) -> GateResult:
    problems = stale_problems(pages, docs_dir)
    return GateResult(
        name="generated pages not stale",
        ok=not problems,
        problems=problems,
        detail=f"{len(GENERATED_PAGES)} generated pages compared",
    )


def _gate_links(docs_dir: Path) -> GateResult:
    if not docs_dir.is_dir():
        return GateResult(name="in-site links", ok=True, skipped=True, detail="no docs directory")
    report = links_mod.check_site(docs_dir)
    return GateResult(
        name="in-site links",
        ok=report.ok,
        problems=[str(p) for p in report.problems],
        detail=f"{report.checked_links} in-site links resolved, {report.external_links} external links not fetched",
    )


def _gate_readability(
    scores: list[readability_mod.ReadabilityScore],
) -> tuple[GateResult, list[readability_mod.ReadabilityScore]]:
    summary = readability_mod.summarise(scores)
    problems: list[str] = []
    for score in scores:
        if not score.present:
            problems.append(f"{score.page}: page missing, readability not measured")
        elif not score.meets_target:
            problems.append(f"{score.page}: Flesch {score.flesch:.1f} below target {READABILITY_TARGET}")
    gate = GateResult(
        name="literacy page readability",
        ok=not problems,
        problems=problems,
        detail=(
            f"{summary['measured']}/{summary['pages']} measured, "
            f"min {summary['min']}, mean {summary['mean']}, target {READABILITY_TARGET}"
        ),
    )
    return gate, scores


def run_all(project_dir: Path | None = None, write: bool = False) -> CheckRun:
    """Run every gate.

    Read-only by default: the staleness gate compares freshly rendered pages
    against what is on disk, so ``check`` reports stale files instead of quietly
    fixing them. Pass ``write=True`` to regenerate them first.
    """
    project_dir = project_dir or PROJECT_DIR
    docs_dir = project_dir / "docs"
    glossary_yml = project_dir / GLOSSARY_YML.name
    metrics_yml = project_dir / METRICS_YML.name

    registry = metrics_mod.load_registry(metrics_yml)
    gloss = glossary_mod.load_glossary(glossary_yml)
    kpis, handoffs = load_scan()
    pages = render_pages(metrics_yml=metrics_yml, glossary_yml=glossary_yml)
    stale_gate = _gate_stale(pages, docs_dir)
    written = write_pages(pages, docs_dir) if write else []
    readability_gate, scores = _gate_readability(readability_mod.score_literacy_pages(project_dir, LITERACY_PAGES))

    gates = [
        _gate_metrics(registry, gloss, project_dir),
        _gate_glossary(gloss, registry),
        _gate_scan_scope(handoffs),
        _gate_coverage(registry, kpis, gloss),
        stale_gate,
        _gate_links(docs_dir),
        readability_gate,
    ]
    return CheckRun(
        gates=gates,
        kpi_count=len({k.name for k in kpis}),
        readability=scores,
        readability_summary=readability_mod.summarise(scores),
        generated_written=written,
    )
