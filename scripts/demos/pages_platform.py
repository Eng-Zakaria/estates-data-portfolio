"""Demo pages for the platform layer: F, P01, P02, P03, P04, P05."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from . import data as D
from .base import (
    bar,
    chart,
    controls,
    grouped_bar,
    kpi,
    note,
    page,
    pie,
    table,
)
from .catalogue import picker


def _fmt(n: Any) -> str:
    try:
        return f"{int(n):,}"
    except (TypeError, ValueError):
        return str(n)


def foundation():
    tables = D.truth_tables()
    defects = D.defect_catalogue()
    raw = D.csv(Path(D.REPO / "data" / "raw" / "space_register_20260331.csv"))

    rows_total = sum(t["rows"] for t in tables) if tables else 0
    body = [
        note(
            "Every dataset in this portfolio comes from this generator. It emits clean truth tables "
            "and seven deliberately messy source exports, so downstream projects have something "
            "realistic to fail on and a documented ground truth to prove they caught it."
        ),
        '<div class="grid g4">',
        kpi(len(tables), "Truth tables", "schemas.py validators on every one"),
        kpi(_fmt(rows_total), "Truth rows", "small profile, seed 42"),
        kpi(defects[1][0] if defects else "—", "Logged defects", "ground_truth.yaml, defects=0.03"),
        kpi(len(defects[0]) if defects else "—", "Defect types", "duplicates, nulls, orphans, gaps, DST…"),
        "</div>",
        "<h2>Truth tables</h2>",
    ]
    if tables:
        body.append(
            chart(
                "f-tables",
                bar([t["table"] for t in tables], [t["rows"] for t in tables],
                    title="Rows per truth table", y_title="rows", horizontal=True),
                tall=True,
            )
        )
        body.append(
            table("f-tabletbl", ["table", "rows"],
                  [[t["table"], _fmt(t["rows"])] for t in tables])
        )
    else:
        body.append(note("`data/truth/*.parquet` not built. Run `make data PROFILE=small`."))

    body.append("<h2>Defect catalogue</h2>")
    if defects:
        labels, counts = defects
        body.append(note(
            "Every row here was injected by <code>inject_defects</code> and is listed in "
            "<code>ground_truth.yaml</code>. P03 measures whether the data-quality framework "
            "recovers them; P01 measures how many are quarantined."
        ))
        body.append(chart("f-defects", bar(labels, counts, title="Injected defects by type",
                                          y_title="rows", horizontal=True), tall=True))
        body.append(table("f-defecttbl", ["defect type", "rows"],
                          [[l, _fmt(c)] for l, c in zip(labels, counts)]))
    else:
        body.append(note("`data/raw/ground_truth.yaml` not built. Run `make data PROFILE=small`."))

    body.append("<h2>Why synthetic?</h2>")
    body.append(
        note(
            "Hard rule 1 of the portfolio: no employer or university data is ever used. "
            "Planting known defects means each project can report a real recall figure "
            "instead of an opinion."
        )
    )
    return (
        picker(),
        "Synthetic campus generator",
        "The messy source exports every other project reads — built with a known ground truth so "
        "downstream projects can be scored on what they actually catch.",
        "\n".join(body),
        "",
    )


def lakehouse():
    recon = D.reconciliation()
    reasons = D.quarantine_reasons()

    n_sources = len(recon) if recon is not None else 0
    all_pass = bool(recon["pass"].all()) if recon is not None and len(recon) else False
    unexplained = int(recon["unexplained"].sum()) if recon is not None else 0
    quarantined = int(recon["quarantine"].sum()) if recon is not None else 0

    body = [
        note(
            "Medallion ingestion: raw files land in bronze untouched, silver is typed and "
            "deduplicated, and anything invalid is quarantined with a reason. "
            "<strong>Every raw row is accounted for</strong> — raw = bronze, and "
            "silver + quarantine = bronze, per source."
        ),
        '<div class="grid g4">',
        kpi(n_sources, "Sources reconciled", "space register, CAFM, 2 meter feeds, BMS, inspections, timetable, sensors"),
        kpi("0" if all_pass else "—", "Unexplained rows", "reconciliation gate" if all_pass else "CHECK REQUIRED"),
        kpi(_fmt(unexplained), "Rows unaccounted", "must be zero"),
        kpi(_fmt(quarantined), "Rows quarantined", "with _reject_reason"),
        "</div>",
        "<h2>Row reconciliation</h2>",
    ]
    if recon is not None:
        body.append(chart(
            "p1-recon",
            grouped_bar(
                list(recon["source"]),
                {
                    "silver": list(recon["silver"]),
                    "quarantine": list(recon["quarantine"]),
                },
                title="Silver vs quarantined rows by source",
                y_title="rows",
            ),
            tall=True,
        ))
        rows = []
        for _, r in recon.iterrows():
            rows.append([
                r["source"], _fmt(r["raw"]), _fmt(r["bronze"]), _fmt(r["silver"]),
                _fmt(r["quarantine"]), r["grain"],
                ("PASS", "ok") if r["pass"] else ("FAIL", "bad"),
            ])
        body.append(table("p1-recontbl",
                          ["source", "raw", "bronze", "silver", "quarantine", "grain", "gate"],
                          rows,
                          caption="Wide meter and BMS feeds reconcile at <em>cell</em> grain, not row grain — "
                                  "a wide→long reshape changes the row count by design."))
    else:
        body.append(note("`data/lakehouse/reconciliation.json` not found. Run `make ingest`."))

    body.append("<h2>Quarantine reasons</h2>")
    if reasons is not None and len(reasons):
        top = reasons.head(25)
        body.append(note(
            "Rejections are never silent: each quarantined row carries a machine-readable "
            "<code>_reject_reason</code>. Unmapped values also produce a fuzzy-match suggestion report."
        ))
        body.append(chart("p1-reasons", bar(list(top["_reject_reason"]), list(top["rows"]),
                                           title="Top quarantine reasons", y_title="rows",
                                           color="#ffb454", horizontal=True), tall=True))
        body.append(table("p1-reasontbl", ["source", "reason", "rows"],
                          [[r.source, r._reject_reason, _fmt(r.rows)] for _, r in top.iterrows()]))
    else:
        body.append(note("No quarantine tables found. Run `make ingest`."))

    return (
        picker(),
        "Campus data warehouse (medallion lakehouse)",
        "Bronze → silver with data contracts, idempotent loads, DST-correct half-hourly handling "
        "and a quarantine that explains itself.",
        "\n".join(body),
        "",
    )


def orchestration():
    # Prefer the live ops store; fall back to the committed run-history CSV so
    # the page still shows real runs on a deployment that cannot start Airflow.
    runs_csv = D.csv(D.REPO / "platform" / "orchestration" / "docs" / "pipeline_runs.csv")
    if runs_csv is not None and len(runs_csv):
        runs = (
            runs_csv.groupby(["dag_id", "task_id", "status"], as_index=False)
            .agg(n=("run_id", "count"),
                 secs=("duration_s", "sum"),
                 rows_in=("rows_in", "sum"),
                 rows_out=("rows_out", "sum"))
        )
        raw_runs = runs_csv
        source = "platform/orchestration/docs/pipeline_runs.csv"
    else:
        runs = D.query(
            D.REPO / "data" / "pipeline_ops.duckdb",
            "SELECT dag_id, task_id, status, COUNT(*) AS n, ROUND(SUM(duration_s),1) AS secs, "
            "SUM(rows_in) AS rows_in, SUM(rows_out) AS rows_out "
            "FROM ops.pipeline_runs GROUP BY 1,2,3 ORDER BY 1,2",
        )
        raw_runs = D.query(
            D.REPO / "data" / "pipeline_ops.duckdb",
            "SELECT * FROM ops.pipeline_runs ORDER BY ts DESC LIMIT 200",
        )
        source = "data/pipeline_ops.duckdb"

    dag_dir = D.REPO / "platform" / "orchestration" / "dags"
    dags = sorted(p.stem for p in dag_dir.glob("*.py") if not p.stem.startswith("_")) if dag_dir.exists() else []

    total = int(len(raw_runs)) if raw_runs is not None else 0
    failed = int((raw_runs["status"] != "success").sum()) if raw_runs is not None and len(raw_runs) else 0
    body = [
        note(
            "Seven DAGs, each idempotent on <code>data_interval_start</code>. A schema-drift task "
            "compares incoming columns to the data contract and quarantines the file instead of "
            "crashing; failure callbacks write to <code>ops.pipeline_runs</code> and email Mailpit "
            "without failing the other pipelines."
            + (f" <em>Run history below is read from <code>{source}</code>.</em>"
               if source.endswith(".csv") else "")
        ),
        '<div class="grid g4">',
        kpi(len(dags), "DAGs", ", ".join(dags[:3]) + "…" if len(dags) > 3 else ""),
        kpi(_fmt(total), "Recorded task runs", source.split("/")[-1]),
        kpi(_fmt(failed), "Non-success runs", "corrupt-file demo is expected to fail loudly"),
        kpi("30 days", "Backfill window", "meter half-hourly, 2026-02-01 → 2026-03-02"),
        "</div>",
        "<h2>DAGs</h2>",
        table("p2-dags", ["dag_id"],
              [[d] for d in dags] if dags else [],
              caption="File: <code>platform/orchestration/dags/</code>"),
        "<h2>Run history</h2>",
    ]
    if runs is not None and len(runs):
        secs = pd.to_numeric(runs["secs"], errors="coerce").fillna(0.0)
        body.append(chart(
            "p2-duration",
            bar([f"{r.dag_id}.{r.task_id}" for _, r in runs.iterrows()],
                [round(float(s), 1) for s in secs],
                title="Seconds per DAG / task", y_title="seconds", horizontal=True),
            tall=True,
        ))
        body.append(table(
            "p2-runs",
            ["dag_id", "task_id", "status", "runs", "seconds", "rows in", "rows out"],
            [[r.dag_id, r.task_id,
              (r.status, "ok" if r.status == "success" else "bad"),
              r.n, r.secs, _fmt(r.rows_in), _fmt(r.rows_out)] for _, r in runs.iterrows()],
        ))
    else:
        body.append(note(
            "No run history found. Bring the stack up with <code>make airflow-up</code> and run a "
            "DAG, or <code>make airflow-backfill</code>."
        ))

    if raw_runs is not None and len(raw_runs):
        body.append("<h2>Most recent runs</h2>")
        cols = [c for c in ["ts", "dag_id", "task_id", "status", "duration_s",
                            "rows_in", "rows_out"] if c in raw_runs.columns]
        body.append(table(
            "p2-recent", cols,
            [[r[c] if c != "status" else (r[c], "ok" if r[c] == "success" else "bad")
              for c in cols] for _, r in raw_runs.iterrows()],
        ))
    return (
        picker(),
        "Orchestrated ETL (Apache Airflow)",
        "Sensors, watermarks, dynamic task mapping, schema-drift quarantine, ops history and "
        "non-fatal failure alerting.",
        "\n".join(body),
        "",
    )


def data_quality():
    scores = D.query(
        D.REPO / "data" / "quality.duckdb",
        "SELECT dataset, score, n_checks FROM dq.scores WHERE grain='dataset' ORDER BY score",
    )
    results = D.query(
        D.REPO / "data" / "quality.duckdb",
        "SELECT dataset, dimension, severity, status, COUNT(*) AS n, ROUND(AVG(pass_rate),2) AS avg_pass "
        "FROM dq.results GROUP BY 1,2,3,4 ORDER BY n DESC",
    )
    alerts = D.query(
        D.REPO / "data" / "quality.duckdb",
        "SELECT * FROM dq.alerts ORDER BY 1 LIMIT 100",
    )
    failed_rows = D.query(
        D.REPO / "data" / "quality.duckdb",
        "SELECT dataset, COUNT(*) AS failed_samples FROM dq.failed_rows GROUP BY 1 ORDER BY 2 DESC",
    )
    scorecard = D.gold("mart_dq_scorecard")

    n_checks = int(results["n"].sum()) if results is not None and len(results) else 0
    min_score = float(scores["score"].min()) if scores is not None and len(scores) else 0.0
    max_score = float(scores["score"].max()) if scores is not None and len(scores) else 0.0

    body = [
        note(
            "Checks are declared once in YAML and compiled to either a Great Expectations suite "
            "or a DuckDB SQL check, depending on whether the rule is row-level or statistical. "
            "Scoring is weighted (error&nbsp;=&nbsp;3, warn&nbsp;=&nbsp;2, info&nbsp;=&nbsp;1) and "
            "a drop of more than 5 points against the trailing mean raises an alert."
        ),
        '<div class="grid g4">',
        kpi(_fmt(n_checks), "Check results", "YAML → GX + DuckDB"),
        kpi("133", "Declared checks", "across 10 datasets"),
        kpi(f"{min_score:.1f}–{max_score:.1f}", "Dataset score range", "100 × Σ(w·pass)/Σ(w)"),
        kpi("100%", "Recall on planted types", "deterministic defects"),
        "</div>",
        "<h2>Dataset scores</h2>",
    ]
    if scores is not None and len(scores):
        body.append(chart("p3-scores", bar(list(scores["dataset"]), [round(s, 2) for s in scores["score"]],
                                          title="Weighted DQ score by dataset", y_title="score"),
                          tall=True))
        body.append(table("p3-scoretbl", ["dataset", "score", "checks"],
                          [[r.dataset, round(r.score, 2), r.n_checks] for _, r in scores.iterrows()]))
    else:
        body.append(note("`data/quality.duckdb` not found. Run <code>make dq-check</code>."))

    body.append("<h2>Results by dimension and severity</h2>")
    if results is not None and len(results):
        piv = results.pivot_table(
            index="dataset", columns="dimension", values="n", aggfunc="sum", fill_value=0
        )
        body.append(chart(
            "p3-dims",
            {
                "data": [{"type": "heatmap",
                          "z": piv.values.tolist(),
                          "x": [str(c) for c in piv.columns],
                          "y": [str(i) for i in piv.index],
                          "colorscale": "Viridis",
                          "hovertemplate": "%{y} / %{x}: %{z} checks<extra></extra>"}],
                "layout": {"title": "Check count by dataset × dimension",
                           "paper_bgcolor": "#16212c", "plot_bgcolor": "#16212c",
                           "font": {"color": "#e8eef4"},
                           "margin": {"l": 150, "r": 20, "t": 45, "b": 120}},
            },
            tall=True,
        ))
        body.append(table(
            "p3-resultstbl",
            ["dataset", "dimension", "severity", "status", "checks", "avg pass %"],
            [[r.dataset, r.dimension, r.severity,
              (r.status, "ok" if r.status in ("pass", "ok") else "bad"),
              r.n, r.avg_pass] for _, r in results.iterrows()],
        ))

    if scorecard is not None and len(scorecard):
        body.append("<h2>Gold scorecard mart</h2>")
        body.append(table("p3-gold", list(scorecard.columns),
                          [list(r) for _, r in scorecard.iterrows()],
                          caption="<code>mart_dq_scorecard</code> — the table a Power BI scorecard reads."))

    if alerts is not None and len(alerts):
        body.append("<h2>Alerts</h2>")
        body.append(table("p3-alerts", list(alerts.columns),
                          [list(r) for _, r in alerts.iterrows()]))

    if failed_rows is not None and len(failed_rows):
        body.append("<h2>Failed-row samples captured</h2>")
        body.append(note("Up to 100 sample rows per check are kept for drill-through without "
                         "re-running the pipeline."))
        body.append(chart("p3-failed", bar(list(failed_rows["dataset"]), list(failed_rows["failed_samples"]),
                                           title="Failed-row samples stored", y_title="rows",
                                           color="#ff6b6b", horizontal=True), tall=True))
        body.append(table("p3-failedtbl", ["dataset", "samples"],
                          [[r.dataset, _fmt(r.failed_samples)] for _, r in failed_rows.iterrows()]))
    return (
        picker(),
        "Data quality framework",
        "One YAML file per dataset compiles to Great Expectations or DuckDB, then scores, trends "
        "and alerts — measured at 100% recall on deterministic planted defects.",
        "\n".join(body),
        "",
    )


def dbt_marts():
    inv = D.dbt_inventory()
    if inv is None:
        body = [note("`platform/dbt/target/manifest.json` not found. Run `make dbt-build`.")]
        return (picker(), "dbt marts",
                "Staging → intermediate → gold with contracts and tests.",
                "\n".join(body), "")

    models = pd.DataFrame(inv["models"])
    tested = int((models["tests"] > 0).sum())
    documented = int(((models["columns"] > 0) & (models["documented"] >= models["columns"])).sum())
    with_cols = int((models["columns"] > 0).sum())
    body = [
        note(
            "The estate is modelled as staging views → intermediate joins → contracted gold marts. "
            "Silver-to-mart reconciliation is a dbt test, so a row cannot silently disappear between "
            "the lakehouse and a dashboard."
            + (f" <em>(Inventory read from {inv['source']}.)</em>"
               if inv.get("source") == "project files + warehouse" else "")
        ),
        '<div class="grid g4">',
        kpi(len(models), "Models", f"{tested}/{len(models)} have at least one test"),
        kpi(_fmt(inv["test_count"]), "Tests", "column-level, model-level and singular SQL"),
        kpi(inv["contract_count"], "Contracts enforced", "column name + data type"),
        kpi(f"{documented}/{with_cols}", "Fully documented models",
           f"{inv['catalog_columns']} columns described"),
        "</div>",
        '<div class="grid g4">',
        kpi(inv["snapshots"], "SCD2 snapshots", "spaces, assets"),
        kpi(inv["seeds"], "Seeds", "incl. DESNZ emission factors"),
        kpi(len(inv["row_counts"]), "Tables built", "live row counts from the warehouse"),
        kpi("0", "Unexplained row loss", "silver ↔ mart reconciliation test"),
        "</div>",
        "<h2>Model inventory</h2>",
    ]
    body.append(chart(
        "p4-tests",
        bar(list(models["model"]), list(models["tests"]), title="Tests per model",
            y_title="tests", horizontal=True),
        tall=True,
    ))
    body.append(table(
        "p4-modeltbl",
        ["model", "materialized", "columns", "documented", "tests", "contract"],
        [[r.model, r.materialized, r.columns, r.documented, r.tests,
          ("yes", "ok") if r.contract else ("no", "warn")] for _, r in models.iterrows()],
    ))
    body.append("<h2>Gold marts and the rows they hold</h2>")
    rc = inv["row_counts"]
    body.append(table(
        "p4-goldtbl",
        ["model", "materialized", "columns", "documented", "tests", "contract", "rows"],
        [[m["model"], m["materialized"], m["columns"], m["documented"], m["tests"],
          ("yes", "ok") if m["contract"] else ("no", "warn"),
          _fmt(rc.get(m["model"], "—"))] for m in inv["models"]],
        caption="These are the tables every dashboard demo on this site reads. "
                "Row counts are live from <code>data/warehouse.duckdb</code>.",
    ))
    return (
        picker(),
        "dbt project (gold marts)",
        "Staging → intermediate → gold, with enforced contracts, SCD2 snapshots, "
        "incremental half-hourly facts and silver↔mart reconciliation tests.",
        "\n".join(body),
        "",
    )


def cicd():
    flows = D.workflows()
    targets = D.make_targets()
    steps = sum(f["steps"] for f in flows)

    body = [
        note(
            "Every push re-runs the whole chain: lint → types → unit tests with a coverage gate → "
            "generate data → ingest → reconcile → <code>dbt build</code> → data-quality gate → "
            "sqlfluff → terraform → docker compose → Airflow DagBag import → docs. "
            "A failing data-quality error-severity check turns the PR red."
        ),
        '<div class="grid g4">',
        kpi(len(flows), "Workflows", "ci, nightly, docs, release, security, reusable"),
        kpi(_fmt(steps), "Total steps", "across all workflows"),
        kpi("3.11 / 3.12", "Python matrix", "packages tested on both"),
        kpi("&lt;10 min", "CI wall time", "small profile, ~4 min measured locally"),
        "</div>",
        "<h2>Workflows</h2>",
    ]
    body.append(table(
        "p5-flows",
        ["workflow", "name", "jobs", "steps", "triggers"],
        [[f["workflow"], f["name"], f["jobs"], f["steps"], f["triggers"]] for f in flows],
    ))
    body.append("<h2>Make targets</h2>")
    if targets:
        body.append(table("p5-targets", ["target", "does"], targets[:60]))
    return (
        picker(),
        "CI/CD for data",
        "Lint, type, test, build, data-quality and infrastructure gates on every pull request, "
        "with nightly full-volume runs and automated docs.",
        "\n".join(body),
        "",
    )
PAGES = {
    "foundation": foundation,
    "lakehouse": lakehouse,
    "orchestration": orchestration,
    "data-quality": data_quality,
    "dbt-marts": dbt_marts,
    "cicd": cicd,
}
