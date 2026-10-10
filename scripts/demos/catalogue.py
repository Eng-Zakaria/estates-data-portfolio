"""The 20 portfolio projects, their demo page slug and one-line purpose.

`HAS_DEMO` marks the projects that get a purpose-built interactive page; every
other project still appears in the picker and index so the nav is complete.
"""

from __future__ import annotations

# (id, label, slug, blurb, has_demo)
PROJECTS: list[tuple[str, str, str, str, bool]] = [
    ("F", "F · Synthetic generator", "foundation",
     "Generates the messy campus source exports every other project reads, with a known ground truth.", True),
    ("P01", "P01 · Lakehouse", "lakehouse",
     "Bronze → silver medallion ingestion with data contracts, idempotency and quarantine.", True),
    ("P02", "P02 · Airflow orchestration", "orchestration",
     "Seven DAGs, watermarks, schema-drift quarantine and failure alerting.", True),
    ("P03", "P03 · Data quality", "data-quality",
     "133 YAML checks compiled to Great Expectations and DuckDB, with scoring, recall and alerts.", True),
    ("P04", "P04 · dbt marts", "dbt-marts",
     "Staging → intermediate → gold marts with contracts, snapshots and reconciliation tests.", True),
    ("P05", "P05 · CI/CD", "cicd",
     "GitHub Actions gates: lint, types, tests, dbt build, DQ, terraform, docs.", True),
    ("P06", "P06 · Space utilisation", "space-utilisation",
     "Frequency × occupancy from timetable plus observed sensor occupancy.", True),
    ("P07", "P07 · Assets & maintenance", "assets-maintenance",
     "Backlog, SLA, reliability, lifecycle and renewal forecast from CAFM-style work orders.", True),
    ("P08", "P08 · Net zero & carbon", "net-zero-carbon",
     "Scope 1/2, intensity, pathway variance and overnight baseload from meter data.", True),
    ("P09", "P09 · Compliance tracker", "compliance",
     "Statutory inspection status, risk scoring, trend and a weekly HTML digest.", True),
    ("P10", "P10 · Institutional return", "institutional-return",
     "Mock HESA EMR / TRAC-style return: mapping, validation, cost allocation, audit trail.", True),
    ("P11", "P11 · IFC analytics", "ifc-analytics",
     "IFC → analytical tables with a model QA report and reconciliation against the space register.", True),
    ("P12", "P12 · COBie validator", "cobie-validator",
     "Rules-driven COBie workbook validation, readiness score and handover loader.", True),
    ("P13", "P13 · Uniclass mapper", "uniclass-mapper",
     "Hybrid fuzzy + embedding classification of messy asset descriptions with a review loop.", True),
    ("P14", "P14 · ISO 19650 checker", "iso19650-checker",
     "Convention-agnostic container naming and metadata checker with fix suggestions and rollback.", True),
    ("P15", "P15 · BMS IoT ingestion", "bms-iot",
     "MQTT → Node-RED → TimescaleDB → Grafana with dead-letter handling and fault monitoring.", True),
    ("P16", "P16 · Energy anomaly", "energy-anomaly",
     "Baselines, MAD / IsolationForest / CUSUM detectors and a prioritised savings action list.", True),
    ("P17", "P17 · Air quality & occupancy", "air-quality",
     "Ventilation risk, thermal comfort, observed occupancy and sensor health.", True),
    ("P18", "P18 · Digital twin layer", "digital-twin",
     "Canonical IDs, a cross-system crosswalk, Brick Schema and a FastAPI context API.", True),
    ("P19", "P19 · Spatial carbon map", "spatial-map",
     "OpenStreetMap footprints joined to synthetic metrics: choropleth, heat clusters, isochrones.", True),
    ("P20", "P20 · Governance & literacy", "governance",
     "Data governance, standards register, metric registry, dashboard guides and a training kit.", True),
]


def picker() -> list[tuple[str, str, str]]:
    """(project_id, label, href) for the nav strip on every demo page."""
    return [(pid, label, f"{slug}.html") for pid, label, slug, _, _ in PROJECTS]