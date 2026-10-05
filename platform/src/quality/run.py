"""P03 runner: evaluate every check, store results, score, alert, extract gold.

Run order per dataset batch: SQL checks, then GX suites (frames from the same
views), then recall checks (which consume both outputs for leak attribution).
``{lake}`` / ``{window_end}`` placeholders in check SQL are substituted here
(plain ``str.replace`` — never ``str.format``, so SQL braces stay literal).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import duckdb
import great_expectations as gx
import pandas as pd

from . import alerts as alerts_mod
from . import gxcompile, gxrun, recall, scoring, sqlchecks, store
from .spec import CheckSpec, load_checks

DATASET_VIEWS = {
    "assets": "truth_assets",
    "spaces_snapshot": "silver_spaces_snapshot",
}

WINDOW_END_DEFAULT = "2026-04-01"


@dataclass
class RunSummary:
    run_id: str
    n_checks: int
    n_fail: int
    n_error_fail: int
    dataset_scores: dict[str, float] = field(default_factory=dict)
    alerts: list[tuple[str, str, str]] = field(default_factory=list)


def substitute(sql: str, lake: str, window_end: str) -> str:
    return sql.replace("{lake}", lake).replace("{window_end}", window_end)


def _sub_spec(spec: CheckSpec, lake: str, window_end: str) -> CheckSpec:
    if spec.engine != "sql":
        return spec
    data = spec.model_dump()
    if data.get("sql_checked"):
        data["sql_checked"] = substitute(data["sql_checked"], lake, window_end)
    if data.get("sql_failed"):
        data["sql_failed"] = substitute(data["sql_failed"], lake, window_end)
    if data.get("sql_checked_by_building"):
        data["sql_checked_by_building"] = substitute(data["sql_checked_by_building"], lake, window_end)
    return CheckSpec(**data)


def _frame_for(con: duckdb.DuckDBPyConnection, dataset: str) -> pd.DataFrame:
    view = DATASET_VIEWS.get(dataset, f"silver_{dataset}")
    return con.execute(f"SELECT * FROM {view}").fetchdf()


def run_all(
    lake: str | Path,
    truth: str | Path,
    ground_truth: str | Path,
    store_path: str | Path,
    gx_root: str | Path,
    gold_dir: str | Path,
    run_id: str,
    profile: str,
    label: str,
    checks_dir: str | Path,
    datasets: list[str] | None = None,
    snap: str | Path | None = None,
    window_end: str = WINDOW_END_DEFAULT,
    build_docs: bool = True,
) -> RunSummary:
    lake_s = str(lake)
    specs = [_sub_spec(s, lake_s, window_end) for s in load_checks(checks_dir)]
    if datasets is not None:
        specs = [s for s in specs if s.dataset in datasets]
    by_id = {s.id: s for s in specs}

    con = store.connect(store_path)
    store.register_views(con, lake, truth, ground_truth, snap)

    outcomes: dict[str, scoring.CheckOutcome] = {}
    gx_samples: dict[str, list[dict]] = {}
    context = None

    # --- SQL checks ---
    for spec in [s for s in specs if s.engine == "sql"]:
        res = sqlchecks.evaluate(con, spec)
        rate = res.pass_rate
        outcomes[spec.id] = scoring.CheckOutcome(
            spec.id,
            spec.dataset,
            spec.dimension,
            spec.severity,
            rate,
            spec.threshold,
            res.by_building,
        )
        _store_result(con, run_id, spec, rate, res.rows_checked, res.rows_failed, res.samples, "sql_rows")

    # --- GX checks ---
    gx_specs = [s for s in specs if s.engine == "gx"]
    if gx_specs:
        # fresh GX project dir per run: suite/VD names are stable, so reusing a
        # dir across runs would collide on add().
        context = gx.get_context(mode="file", project_root_dir=str(Path(gx_root) / run_id))
        _disable_gx_telemetry(context)
        ds = context.data_sources.add_pandas("dq_source")
        suites = gxcompile.compile_suites(gx_specs, con)
        index = gxcompile.build_check_index(gx_specs)
        for suite_name, suite in suites.items():
            dataset = suite_name.split("dq_", 1)[1]
            frame = _frame_for(con, dataset)
            asset = ds.add_dataframe_asset(name=f"asset_{dataset}")
            batch_def = asset.add_batch_definition_whole_dataframe(f"batch_{dataset}")
            for res in gxrun.run_suite(context, batch_def, suite, frame, index[dataset]):
                spec = by_id[res.check_id]
                rate = res.pass_rate
                outcomes[spec.id] = scoring.CheckOutcome(
                    spec.id, spec.dataset, spec.dimension, spec.severity, rate, spec.threshold
                )
                gx_samples[spec.id] = res.samples
                _store_result(con, run_id, spec, rate, res.rows_checked, res.rows_failed, res.samples, "gx_values")
        if build_docs:
            context.build_data_docs()

    # --- recall checks ---
    for spec in [s for s in specs if s.engine == "recall"]:
        res = recall.evaluate(con, spec, by_id, gx_samples, lake_s)
        rate = res.recall
        outcomes[spec.id] = scoring.CheckOutcome(
            spec.id, spec.dataset, spec.dimension, spec.severity, rate, spec.threshold
        )
        _store_result(con, run_id, spec, rate, res.planted, res.rows_failed, res.samples, "recall_keys")

    # --- scores ---
    ds_scores = scoring.dataset_scores(by_id, outcomes)
    dim_scores = scoring.dimension_scores(by_id, outcomes)
    b_scores = scoring.building_scores(by_id, outcomes)
    for dataset, (score, n) in ds_scores.items():
        con.execute("INSERT INTO dq.scores VALUES (?, 'dataset', ?, '', ?, ?)", [run_id, dataset, score, n])
    for (dataset, dim), (score, n) in dim_scores.items():
        con.execute("INSERT INTO dq.scores VALUES (?, 'dimension', ?, ?, ?, ?)", [run_id, dataset, dim, score, n])
    for building, (score, n) in b_scores.items():
        con.execute("INSERT INTO dq.scores VALUES (?, 'building', '', ?, ?, ?)", [run_id, building, score, n])
    con.execute("INSERT INTO dq.runs VALUES (?, CURRENT_TIMESTAMP, ?, ?)", [run_id, profile, label])

    # --- alerts ---
    error_fails = [(cid, o.dataset) for cid, o in outcomes.items() if o.severity == "error" and o.status == "fail"]
    raised = alerts_mod.evaluate_alerts(con, run_id, {d: s for d, (s, _) in ds_scores.items()}, error_fails)

    # --- gold extracts (Power BI handoff reads these) ---
    gold = Path(gold_dir)
    gold.mkdir(parents=True, exist_ok=True)
    for table, name in [("dq.results", "dq_results"), ("dq.scores", "dq_scores"), ("dq.alerts", "dq_alerts")]:
        df = con.execute(f"SELECT * FROM {table} WHERE run_id = ?", [run_id]).fetchdf()
        df.to_parquet(gold / f"{name}.parquet", index=False)
        df.to_csv(gold / f"{name}.csv", index=False)
    failed = con.execute("SELECT check_id, row_json FROM dq.failed_rows WHERE run_id = ?", [run_id]).fetchdf()
    failed.to_parquet(gold / "dq_failed_rows.parquet", index=False)
    failed.to_csv(gold / "dq_failed_rows.csv", index=False)

    _write_provenance(gold, run_id, lake_s, str(truth), str(ground_truth), profile, label, len(specs))

    n_fail = sum(1 for o in outcomes.values() if o.status == "fail")
    return RunSummary(run_id, len(specs), n_fail, len(error_fails), {d: s for d, (s, _) in ds_scores.items()}, raised)


def _store_result(con, run_id, spec, rate, checked, failed, samples, kind) -> None:
    status = "pass" if rate * 100.0 >= spec.threshold else "fail"
    con.execute(
        "INSERT INTO dq.results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [
            run_id,
            spec.dataset,
            spec.id,
            spec.dimension,
            spec.severity,
            spec.engine,
            checked,
            failed,
            rate,
            spec.threshold,
            status,
        ],
    )
    for row in samples:
        con.execute(
            "INSERT INTO dq.failed_rows VALUES (?, ?, ?, ?)",
            [run_id, spec.id, kind, sqlchecks.row_to_json(row)],
        )


def _disable_gx_telemetry(context: gx.DataContext) -> None:
    try:
        context.variables.anonymous_usage_statistics.enabled = False  # type: ignore[union-attr]
    except Exception:
        pass


def _write_provenance(
    gold: Path, run_id: str, lake: str, truth: str, ground_truth: str, profile: str, label: str, n_checks: int
) -> None:
    inputs: dict[str, dict[str, object]] = {}
    for name, base in [("lake", lake), ("truth", truth)]:
        files = sorted(str(p) for p in Path(base).rglob("*") if p.is_file())
        inputs[name] = {"path": base, "n_files": len(files)}
    doc = {
        "run_id": run_id,
        "profile": profile,
        "label": label,
        "n_checks": n_checks,
        "window_end": WINDOW_END_DEFAULT,
        "inputs": inputs,
        "ground_truth": ground_truth,
        "synthetic_note": "All data synthetic (campus_synth) or derived; no real estate data.",
    }
    (gold / f"provenance_{run_id}.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
