"""Paths and policy constants for the P20 governance and literacy pack.

Everything is derived from this file's location so the pack can be built from
any working directory, and so tests can point at a fixture tree.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_DIR: Path = Path(__file__).resolve().parents[1]
REPO_ROOT: Path = PROJECT_DIR.parents[1]
DOCS_DIR: Path = PROJECT_DIR / "docs"
GENERATED_DIR: Path = DOCS_DIR / "generated"
METRICS_YML: Path = PROJECT_DIR / "metrics.yml"
GLOSSARY_YML: Path = PROJECT_DIR / "glossary.yml"
RACI_YML: Path = PROJECT_DIR / "raci.yml"
STANDARDS_YML: Path = PROJECT_DIR / "standards.yml"
DBT_MODELS_DIR: Path = REPO_ROOT / "platform" / "dbt" / "models"
DQ_SCORES_CSV: Path = REPO_ROOT / "data" / "quality" / "gold" / "dq_scores.csv"
DQ_RESULTS_CSV: Path = REPO_ROOT / "data" / "quality" / "gold" / "dq_results.csv"
DQ_ALERTS_CSV: Path = REPO_ROOT / "data" / "quality" / "gold" / "dq_alerts.csv"
WAREHOUSE_DB: Path = REPO_ROOT / "data" / "warehouse.duckdb"
PROJECTS_DIR: Path = REPO_ROOT / "projects"

#: Projects whose Power BI handoff (or KPI helper module) is scanned for KPI names.
#: Anything else that ships a `powerbi/measures.dax` must be added here or listed in
#: ``SCAN_EXCLUSIONS`` with a reason: tests/test_metrics.py enforces both, so a new
#: dashboard cannot silently escape registry coverage.
SCAN_SCOPE: tuple[str, ...] = ("p06", "p07", "p08", "p09", "p10", "p11")

#: project id -> why it is not scanned yet.
SCAN_EXCLUSIONS: dict[str, str] = {
    "p16": "energy anomaly project is mid-build (uncommitted); registry entries land with its handover",
}

#: Relative to the repository root. Consumers listed in metrics.yml must be one of these.
PLATFORM_CONSUMERS: tuple[str, ...] = ("p03",)

#: Pages scored for readability. Plain English guides only: technical generated
#: pages (dictionary, lineage) are excluded on purpose and say so.
LITERACY_PAGES: tuple[str, ...] = (
    "docs/dashboards/index.md",
    "docs/dashboards/p06-space-utilisation.md",
    "docs/dashboards/p07-assets-and-maintenance.md",
    "docs/dashboards/p08-energy-and-carbon.md",
    "docs/dashboards/p09-compliance.md",
    "docs/dashboards/p10-institutional-return.md",
    "docs/dashboards/data-quality-scorecard.md",
    "docs/training/ten-minute-demo.md",
    "docs/training/workshop.md",
    "docs/training/exercises.md",
    "docs/training/quiz.md",
    "docs/training/answer-key.md",
    "docs/training/feedback-form.md",
    "docs/training/slide-outline.md",
    "docs/training/facilitator-notes.md",
)

#: Flesch reading ease target for the literacy pages (spec: report >= 50).
READABILITY_TARGET: float = 50.0

#: Generated pages that must be byte-identical to a fresh generation.
GENERATED_PAGES: tuple[str, ...] = (
    "generated/data-dictionary.md",
    "generated/lineage.md",
    "generated/dq-scores.md",
    "generated/glossary.md",
    "generated/metric-registry.md",
    "generated/standards-register.md",
    "generated/raci.md",
)

GENERATED_BANNER = (
    "<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). "
    "CI fails if this page is stale. -->"
)

SYNTHETIC_NOTE = (
    "All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any "
    "real university, building or estate, and nothing here is a compliance statement."
)