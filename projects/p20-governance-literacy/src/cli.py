"""Command line for the P20 governance and literacy pack.

    python -m src.cli build        # regenerate the generated pages
    python -m src.cli check        # every gate; non-zero exit on failure
    python -m src.cli readability  # Flesch reading ease per literacy page
    python -m src.cli coverage     # registry and glossary coverage of dashboard KPIs
    python -m src.cli links        # in-site link report
"""

from __future__ import annotations

import typer

import checks
import dashboards
import glossary as glossary_mod
import links as links_mod
import metrics as metrics_mod
import readability as readability_mod
from config import (
    GENERATED_PAGES,
    GLOSSARY_YML,
    LITERACY_PAGES,
    METRICS_YML,
    PROJECT_DIR,
    READABILITY_TARGET,
    REPO_ROOT,
    SCAN_SCOPE,
)

app = typer.Typer(add_completion=False, help="P20 governance and literacy pack tooling.")


@app.command()
def build() -> None:
    """Regenerate the generated pages from dbt, P03 output and the YAML sources."""
    pages = checks.render_pages()
    written = checks.write_pages(pages, PROJECT_DIR / "docs")
    for rel in sorted(pages):
        state = "updated" if rel in written else "unchanged"
        print(f"{state:9} docs/{rel}")
    print(f"\n{len(written)} of {len(pages)} generated pages updated.")


@app.command()
def check() -> None:
    """Run every governance gate. Exits non-zero if any gate fails."""
    run = checks.run_all()
    for gate in run.gates:
        print(str(gate))
    summary = run.readability_summary
    print(
        f"\nreadability: {summary['measured']}/{summary['pages']} pages measured, "
        f"min {summary['min']}, mean {summary['mean']}, target {READABILITY_TARGET}"
    )
    print(f"dashboard KPIs covered: {run.kpi_count}")
    if run.generated_written:
        print(f"regenerated during check (unexpected in check mode): {run.generated_written}")
    if run.ok:
        print("\nP20 checks passed.")
        raise typer.Exit(0)
    print(f"\n{len(run.failures())} gate(s) failed.")
    raise typer.Exit(1)


@app.command()
def readability() -> None:
    """Print Flesch reading ease for every plain-English guide."""
    scores = readability_mod.score_literacy_pages(PROJECT_DIR, LITERACY_PAGES)
    print(f"{'page':60} {'Flesch':>8} {'words':>6}  status")
    for score in scores:
        value = "n/a" if score.flesch is None else f"{score.flesch:.1f}"
        status = "missing" if not score.present else ("ok" if score.meets_target else "below target")
        print(f"{score.page:58} {value:>8} {score.words:>6}  {status}")
    summary = readability_mod.summarise(scores)
    print(f"\nmeasured {summary['measured']}/{summary['pages']}, min {summary['min']}, mean {summary['mean']}")


@app.command()
def coverage() -> None:
    """Show how dashboard KPIs map to the metric registry and the glossary."""
    registry = metrics_mod.load_registry(METRICS_YML)
    gloss = glossary_mod.load_glossary(GLOSSARY_YML)
    scope = SCAN_SCOPE
    handoffs = dashboards.projects_with_handoff(PROJECT_DIR.parent)
    kpis = dashboards.scan_projects(PROJECT_DIR.parent, REPO_ROOT, scope)
    print(f"{len(handoffs)} hand-off file(s) scanned: {sorted(handoffs)}")
    print(f"{len({k.name for k in kpis})} distinct KPI names published by dashboards")
    print(f"{len(registry.metrics)} registry entries ({len(registry.live)} live, {len(registry.planned)} planned)")
    print(f"{len(gloss.terms)} glossary terms, {len(gloss.kpi_aliases)} KPI aliases")
    problems = metrics_mod.coverage_problems(registry, kpis) + glossary_mod.coverage_problems(gloss, kpis)
    if problems:
        print("\nproblems:")
        for problem in problems:
            print(f"  - {problem}")
        raise typer.Exit(1)
    print("\ncoverage is complete in both directions.")


@app.command()
def links() -> None:
    """Resolve every in-site link and anchor; report external links without fetching."""
    report = links_mod.check_site(PROJECT_DIR / "docs")
    for problem in report.problems:
        print(str(problem))
    print(
        f"\n{report.checked_links} in-site links checked, {len(report.problems)} problem(s), "
        f"{report.external_links} external link(s) not fetched (offline by design)"
    )
    if not report.ok:
        raise typer.Exit(1)


@app.command("list-generated")
def list_generated() -> None:
    """List the generated pages the staleness gate protects."""
    for rel in GENERATED_PAGES:
        print(f"docs/{rel}")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    app()