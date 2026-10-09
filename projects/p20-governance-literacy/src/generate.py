"""Render the generated pages of the P20 site.

Deterministic by design: no timestamps, everything sorted, so
``make p20-check`` can regenerate into a temporary directory and diff the result
against what is committed. Each renderer returns the full page text and takes
its data as arguments, so tests can render from fixtures without touching the
repository.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import dbt_meta
import glossary as glossary_mod
from config import GENERATED_BANNER, SYNTHETIC_NOTE
from metrics import Metric, Registry

LAYER_TITLES = {
    "staging": "Staging (one model per source, renamed and typed)",
    "intermediate": "Intermediate (joined and deduplicated)",
    "marts": "Marts (dimensions, facts and analysis tables the dashboards read)",
    "seeds": "Seeds (reference data committed to the repository)",
    "snapshots": "Snapshots (history captured over time)",
    "other": "Other",
}


def cell(text: str) -> str:
    """Make a value safe for one Markdown table cell."""
    return " ".join(str(text).replace("|", "/").split()) or "-"


def table(headers: list[str], rows: Iterable[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    out.extend("| " + " | ".join(cell(r) for r in row) + " |" for row in rows)
    return "\n".join(out)


def page(title: str, intro: str, body: str) -> str:
    return "\n".join([GENERATED_BANNER, "", f"# {title}", "", intro, "", body, "", SYNTHETIC_NOTE, ""])


# --------------------------------------------------------------- dictionary
def render_dictionary(meta: dbt_meta.DbtMetadata) -> str:
    body: list[str] = []
    total_columns = sum(len(m.columns) for m in meta.models)
    body.append(
        f"Built from the dbt project at `platform/dbt/models` ({meta.source} read, "
        f"{len(meta.models)} models, {total_columns} columns, {len(meta.models)} tables). "
        "Column descriptions come from the YAML in the dbt project, so they are only as good as "
        "the descriptions written there."
    )
    body.append("")
    body.append(table(
        ["Layer", "Models", "Columns"],
        [
            [
                LAYER_TITLES.get(layer, layer),
                str(sum(1 for m in meta.models if m.layer == layer)),
                str(sum(len(m.columns) for m in meta.models if m.layer == layer)),
            ]
            for layer in sorted({m.layer for m in meta.models})
        ],
    ))
    for layer in sorted({m.layer for m in meta.models}):
        body.append("")
        body.append(f"## {LAYER_TITLES.get(layer, layer)}")
        for model in sorted((m for m in meta.models if m.layer == layer), key=lambda m: m.name):
            materialised = f" materialised as `{model.materialization}`" if model.materialization else ""
            body.append("")
            body.append(f"### `{model.name}`")
            body.append("")
            body.append(model.description or "_No description in the dbt project._")
            body.append("")
            if materialised:
                body.append(materialised.capitalize() + ".")
                body.append("")
            if model.depends_on:
                body.append("Reads: " + ", ".join(f"`{d}`" for d in model.depends_on))
                body.append("")
            if model.columns:
                body.append(table(
                    ["Column", "Type", "Description", "Tests"],
                    [[c.name, c.data_type, c.description, ", ".join(c.tests)] for c in model.columns],
                ))
            else:
                body.append("_No columns documented in the dbt YAML._")
    return page("Data dictionary (generated)", "Every table and column the analytics layer exposes.", "\n".join(body))


# ------------------------------------------------------------------ lineage
def render_lineage(meta: dbt_meta.DbtMetadata) -> str:
    edges = meta.edges
    body: list[str] = []
    body.append(
        "Upstream to downstream, read from `{{ ref() }}` and `{{ source() }}` calls in the model SQL "
        f"plus `exposures.yml` ({meta.source} read). {len(edges)} edges over {len(meta.models)} models."
    )
    body.append("")
    body.append("```mermaid")
    body.append("flowchart LR")
    for layer in ("staging", "intermediate", "marts"):
        members = sorted(m.name for m in meta.models if m.layer == layer)
        if members:
            body.append(f'  subgraph {layer}["{layer}"]')
            body.extend(f"    {name}()" for name in members)
            body.append("  end")
    for parent, child in edges:
        body.append(f"  {parent} --> {child}")
    body.append("```")
    body.append("")
    body.append("## Exposure (what the dashboards read)")
    body.append("")
    body.append(table(
        ["Exposure", "Type", "Owner", "Reads"],
        [[e.name, e.type, e.owner, ", ".join(f"`{d}`" for d in e.depends_on)] for e in sorted(meta.exposures, key=lambda e: e.name)],
    ))
    body.append("")
    body.append("## Edges")
    body.append("")
    body.append(table(["Upstream", "Downstream"], [[u, d] for u, d in edges]))
    return page("Lineage (generated)", "Where every table comes from, and what reads it.", "\n".join(body))


# --------------------------------------------------------------- DQ scores
def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def render_dq_scores(scores_path: Path, results_path: Path, alerts_path: Path) -> str:
    score_rows = _read_csv(scores_path)
    result_rows = _read_csv(results_path)
    alert_rows = _read_csv(alerts_path)
    body: list[str] = []

    if not score_rows:
        body.append(
            "**No data quality results in this checkout.** The P03 run has not been executed here, so this "
            "page is empty rather than showing invented numbers. To fill it in:\n\n"
            "```\nmake data && make dq-check\n```\n\n"
            "The DQ framework itself is described in the repository's `docs/dq-policy.md`."
        )
        return page("Data quality scores (generated)", "Measured, not asserted: the numbers come from the P03 run.", "\n".join(body))

    latest = max(row["run_id"] for row in score_rows if row.get("run_id"))
    body.append(f"Run `{latest}`. Scores come from `data/quality/gold/dq_scores.csv`; nothing is recalculated here.")
    body.append("")
    by_dataset: dict[str, dict[str, str]] = {}
    for row in score_rows:
        if row.get("run_id") == latest and row.get("grain") == "dataset":
            by_dataset[row["dataset"]] = row
    body.append("## By dataset")
    body.append("")
    body.append(table(
        ["Dataset", "Score", "Checks", "Read"],
        [
            [
                name,
                f"{float(row['score']):.1f}",
                row.get("n_checks", "-"),
                _score_read(float(row["score"])),
            ]
            for name, row in sorted(by_dataset.items())
        ],
    ))

    dimension_rows = [r for r in score_rows if r.get("run_id") == latest and r.get("grain") == "dimension"]
    if dimension_rows:
        body.append("")
        body.append("## By dataset and dimension")
        body.append("")
        body.append(table(
            ["Dataset", "Dimension", "Score", "Checks"],
            [[r.get("dataset", "-"), r.get("key", "-"), f"{float(r['score']):.1f}", r.get("n_checks", "-")] for r in sorted(dimension_rows, key=lambda r: (r.get("dataset", ""), r.get("key", "")))],
        ))

    failing = [r for r in result_rows if r.get("run_id") == latest and r.get("status") == "fail"]
    body.append("")
    body.append("## Failing checks in this run")
    body.append("")
    if failing:
        body.append(table(
            ["Dataset", "Check", "Dimension", "Severity", "Rows failed", "Rows checked", "Threshold"],
            [
                [r.get("dataset", "-"), r.get("check_id", "-"), r.get("dimension", "-"), r.get("severity", "-"),
                 r.get("rows_failed", "-"), r.get("rows_checked", "-"), r.get("threshold", "-")]
                for r in sorted(failing, key=lambda r: (r.get("severity", ""), r.get("dataset", "")))
            ],
        ))
    else:
        body.append("_No failing checks in this run._")

    body.append("")
    body.append("## Alerts")
    body.append("")
    if alert_rows:
        body.append(table(
            ["Kind", "Dataset", "Detail"],
            [[r.get("alert_kind", "-"), r.get("dataset", "-"), r.get("detail", "-")] for r in alert_rows],
        ))
    else:
        body.append("_No alerts raised._")
    return page("Data quality scores (generated)", "Measured, not asserted: the numbers come from the P03 run.", "\n".join(body))


def _score_read(score: float) -> str:
    if score >= 100:
        return "clean at this window's checks"
    if score >= 95:
        return "small number of failures"
    if score >= 85:
        return "needs attention"
    return "below the 95% review threshold"


# ----------------------------------------------------------------- glossary
def render_glossary(gloss: glossary_mod.Glossary, scores: dict[str, float]) -> str:
    by_id = gloss.by_id()
    body: list[str] = []
    body.append(
        f"{len(gloss.terms)} terms. Definitions are hand-written in `glossary.yml`; the DQ score column is "
        "joined from the P03 run when one exists in this checkout."
    )
    body.append("")
    body.append(table(
        ["Term", "Definition", "Owner", "Source of truth", "Refresh", "DQ score", "Classification"],
        [
            [
                t.term,
                t.definition,
                t.owner,
                t.source_of_truth,
                t.refresh,
                glossary_mod.dq_score_for(t, scores),
                t.classification,
            ]
            for t in sorted(gloss.terms, key=lambda t: t.term.lower())
        ],
    ))
    notes = [t for t in gloss.terms if t.notes]
    if notes:
        body.append("")
        body.append("## Notes and misreadings")
        body.append("")
        for term in sorted(notes, key=lambda t: t.term.lower()):
            body.append(f"- **{term.term}**: {term.notes}")
    body.append("")
    body.append("## Dashboard KPI coverage")
    body.append("")
    body.append(
        table(
            ["Dashboard KPI", "Glossary term"],
            [[kpi, by_id[target].term] for kpi, target in sorted(gloss.kpi_aliases.items())],
        )
        if by_id
        else "_No terms loaded._"
    )
    return page("Business glossary (generated)", "The words estates people use, with owner, source and current quality.", "\n".join(body))


# ----------------------------------------------------------- metric registry
def render_metric_registry(registry: Registry, gloss: glossary_mod.Glossary | None = None) -> str:
    by_id = gloss.by_id() if gloss else {}
    body: list[str] = []
    body.append(
        f"{len(registry.metrics)} entries: {len(registry.live)} published on a dashboard, {len(registry.planned)} planned. "
        "This page is generated from `metrics.yml`, which is the source of truth."
    )
    body.append("")
    body.append(table(
        ["Metric", "Id", "Kind", "Status", "Grain", "Owner", "Version", "Dashboards"],
        [[m.name, m.id, m.kind, m.status, m.grain, m.owner, m.version, ", ".join(m.dashboards)] for m in sorted(registry.metrics, key=lambda m: m.name)],
    ))
    for metric in sorted(registry.metrics, key=lambda m: m.id):
        body.append("")
        body.append(f"## {metric.name}")
        body.append("")
        term = by_id.get(metric.glossary_term)
        body.append(f"- **Definition**: {metric.definition}")
        body.append(f"- **Formula**: `{metric.formula}`")
        body.append(f"- **Grain**: {metric.grain}")
        body.append(f"- **Owner**: `{metric.owner}`")
        body.append(f"- **Source model**: " + (", ".join(f"`{s}`" for s in metric.source_model) or "_none (helper)_"))
        body.append(f"- **Version**: {metric.version}")
        body.append(f"- **Status**: {metric.status} ({'kind: ' + metric.kind})")
        body.append(f"- **Classification**: {metric.classification}")
        body.append(f"- **Dashboards**: " + (", ".join(f"`{d}`" for d in metric.dashboards) or "_none_"))
        if term:
            body.append(f"- **Glossary**: {term.term} - {term.definition}")
        body.append("- **Caveats**:")
        body.extend(f"    - {c}" for c in metric.caveats)
    return page("Metric registry (generated)", "Every published number: what it means, how it is built, what it cannot tell you.", "\n".join(body))


# ------------------------------------------------------- standards register
def render_standards(standards: list[dict]) -> str:
    body: list[str] = []
    body.append(
        f"{len(standards)} standards. Status is honest: `implemented` means a rule or code list from the "
        "official source is encoded and tested here; `mock` means a development placeholder; "
        "`awareness-only` means nothing is stored or applied; `not-obtained` means we wanted it and could not get it."
    )
    body.append("")
    body.append(table(
        ["Standard", "Status", "Where it touches the data", "Owner", "Project", "Source"],
        [[s["name"], s["status"], "; ".join(s["where_it_touches_data"]), s["owner"], s.get("project") or "-", s["url"]] for s in sorted(standards, key=lambda s: s["name"])],
    ))
    for standard in sorted(standards, key=lambda s: s["name"]):
        body.append("")
        body.append(f"## {standard['name']}")
        body.append("")
        body.append(f"- **Status**: `{standard['status']}`")
        body.append(f"- **What it is**: {' '.join(str(standard['what_it_is']).split())}")
        body.append(f"- **Owner**: `{standard['owner']}`")
        body.append(f"- **Source**: {standard['url']}")
        body.append(f"- **Access**: {standard['reference_access']}")
        body.append("- **Where it touches the data**:")
        body.extend(f"    - {w}" for w in standard["where_it_touches_data"])
        body.append(f"- **Limitations**: {' '.join(str(standard['limitations']).split())}")
        if standard.get("provenance"):
            body.append(f"- **Provenance**: `{standard['provenance']}`")
    return page("Standards register (generated)", "What each standard is, where it bites, and how far we have actually got.", "\n".join(body))


# ---------------------------------------------------------------------- RACI
def render_raci(raci: dict) -> str:
    body: list[str] = []
    body.append(
        "Generated from `raci.yml`. **A** is the single accountable role per activity. "
        "Letters: " + ", ".join(f"**{k}** {v}" for k, v in sorted(raci["raci_letters"].items())) + "."
    )
    body.append("")
    body.append("## Roles")
    body.append("")
    body.append(table(
        ["Role", "Accountable for", "Typical person", "Escalates to"],
        [[r["name"], r["accountable_for"], r["typical_person"], r["escalation_to"]] for r in raci["roles"]],
    ))
    for domain in raci["domains"]:
        body.append("")
        body.append(f"## {domain['name']}")
        body.append("")
        body.append(f"Accountable owner: `{domain['accountable']}`. Steward and custodian: `{domain['steward']}`, `{domain['custodian']}`.")
        body.append("")
        body.append(table(
            ["Activity", "Owner", "Steward", "Custodian", "Consumer"],
            [[a["activity"], a["owner"], a["steward"], a["custodian"], a["consumer"]] for a in domain["activities"]],
        ))
        body.append("")
        body.append("**Decision rights**")
        body.append("")
        body.extend(f"- {d}" for d in domain["decision_rights"])
        body.append("")
        body.append("**Escalation path**")
        body.append("")
        body.extend(f"- {e}" for e in domain["escalation"])
    body.append("")
    body.append("## Decision rights that apply everywhere")
    body.append("")
    body.extend(f"- {d}" for d in raci["decision_rights_global"])
    return page("RACI (generated)", "Who does what, who decides, and where problems go.", "\n".join(body))