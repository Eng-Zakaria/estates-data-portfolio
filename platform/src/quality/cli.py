"""P03 CLI: run the DQ framework, score snapshots trend, print digests.

``dq-run`` executes every check (SQL + GX + recall), writes dq.* tables, gold
extracts and Data Docs, prints a score digest, and exits non-zero on any
``error``-severity failure (the CI gate signal consumed by P05).
``dq-trend`` scores the 12 weekly snapshots to show improvement as defects fall.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(no_args_is_help=True)

CHECKS_DIR = Path("platform/quality/checks")


def _run_id(prefix: str) -> str:
    return f"{prefix}_{dt.datetime.now(tz=dt.UTC):%Y%m%d_%H%M%S}"


@app.command("run")
def run_cmd(
    lake: Annotated[str, typer.Option(help="Lakehouse root with silver/quarantine.")] = "data/lakehouse",
    truth: Annotated[str, typer.Option(help="Truth reference root.")] = "data/truth",
    ground_truth: Annotated[str, typer.Option(help="Defect log YAML.")] = "data/raw/ground_truth.yaml",
    store: Annotated[str, typer.Option(help="DQ DuckDB store.")] = "data/quality.duckdb",
    gx_root: Annotated[str, typer.Option(help="GX project root (generated).")] = "data/quality_gx",
    gold: Annotated[str, typer.Option(help="Gold extracts dir.")] = "data/quality/gold",
    profile: Annotated[str, typer.Option()] = "small",
    label: Annotated[str, typer.Option()] = "manual",
    run_id: Annotated[str, typer.Option()] = "",
) -> None:
    """Run every DQ check and print the score digest."""
    from .run import run_all

    rid = run_id or _run_id("dq")
    summary = run_all(
        lake,
        truth,
        ground_truth,
        store,
        gx_root,
        gold,
        rid,
        profile,
        label,
        CHECKS_DIR,
        datasets=[
            "spaces",
            "assets",
            "work_orders",
            "meters_a",
            "meters_b",
            "sensors",
            "bms",
            "inspections",
            "timetable",
        ],
    )
    print(f"run {rid}: {summary.n_checks} checks, {summary.n_fail} failed, {summary.n_error_fail} error-fails")
    for dataset in sorted(summary.dataset_scores):
        print(f"  {dataset:12s} score {summary.dataset_scores[dataset]:6.2f}")
    for kind, dataset, detail in summary.alerts:
        print(f"  ALERT [{kind}] {dataset}: {detail}")
    if summary.n_error_fail:
        raise typer.Exit(code=1)


@app.command("trend")
def trend_cmd(
    snapshots: Annotated[str, typer.Option(help="Weekly snapshots root.")] = "data/raw_snapshots",
    truth: Annotated[str, typer.Option(help="Truth reference root.")] = "data/truth",
    store: Annotated[str, typer.Option(help="DQ DuckDB store.")] = "data/quality.duckdb",
    gx_root: Annotated[str, typer.Option(help="GX project root (generated).")] = "data/quality_gx_trend",
    gold: Annotated[str, typer.Option(help="Gold extracts dir.")] = "data/quality/gold_trend",
    weeks: Annotated[int, typer.Option()] = 12,
) -> None:
    """Score snapshot weeks 01..N with the snapshot checks and print the trend."""
    from .run import run_all

    scores: list[tuple[str, float]] = []
    for week in range(1, weeks + 1):
        snap = str(Path(snapshots) / f"week_{week:02d}")
        rid = f"{_run_id('dqtrend')}_w{week:02d}"
        summary = run_all(
            snapshots,
            truth,
            "",
            store,
            gx_root,
            gold,
            rid,
            "snapshots",
            f"week_{week:02d}",
            CHECKS_DIR,
            datasets=["spaces_snapshot"],
            snap=snap,
            build_docs=False,
        )
        week_score = summary.dataset_scores.get("spaces_snapshot", 0.0)
        scores.append((f"week_{week:02d}", week_score))
        print(f"  week_{week:02d} spaces score {week_score:6.2f}")
    lo, hi = scores[0][1], scores[-1][1]
    print(f"trend: {scores[0][0]} {lo:.2f} -> {scores[-1][0]} {hi:.2f} (delta {hi - lo:+.2f})")
    if hi < lo:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
