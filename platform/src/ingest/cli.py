"""Typer CLI: bronze / silver / run-all / reconcile / catalogue."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import pandas as pd
import typer

from .bronze import load_bronze
from .contracts import generate_catalogue_md
from .reconcile import raw_row_count, reconcile_counts
from .silver_cafm import transform_cafm
from .silver_meters import transform_meter_A, transform_meter_B
from .silver_others import (
    transform_bms,
    transform_inspections,
    transform_sensors,
    transform_timetable,
)
from .silver_space import transform_space
from .storage import resolve_root

app = typer.Typer(no_args_is_help=True)

SOURCES = [
    "space_register",
    "cafm_workorders",
    "meter_hh_supplierA",
    "meter_hh_supplierB",
    "bms_trends",
    "statutory_inspections",
    "timetable",
    "sensors",
]


def _bronze_frame(out_root: Path, source: str) -> pd.DataFrame:
    parts = sorted((out_root / "bronze" / source).rglob("*.parquet"))
    if not parts:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)


@app.command()
def bronze(
    source: Annotated[str, typer.Option(help="contract/source name")] = "cafm_workorders",
    file: Annotated[Path, typer.Option(help="raw file")] = Path("data/raw"),  # noqa: B008
    out: Annotated[Path, typer.Option(help="lakehouse root")] = Path("data/lakehouse"),  # noqa: B008
) -> None:
    root = resolve_root(out)
    dest, entry = load_bronze(source, file, root / "bronze")
    typer.echo(f"{source}: {entry['status']} rows={entry['rows']} -> {dest}")


@app.command()
def silver(
    source: Annotated[str, typer.Option()] = "cafm_workorders",
    out: Annotated[Path, typer.Option()] = Path("data/lakehouse"),  # noqa: B008
    truth: Annotated[Path, typer.Option()] = Path("data/truth/buildings.parquet"),  # noqa: B008
) -> None:
    root = resolve_root(out)
    _run_silver_one(source, root, truth)
    typer.echo(f"silver {source} done")


def _run_silver_one(source: str, root: Path, truth_buildings_path: Path) -> tuple[int, int]:
    bronze_df = _bronze_frame(root, source)
    truth_b = (
        pd.read_parquet(truth_buildings_path)
        if truth_buildings_path.exists()
        else pd.DataFrame(columns=["building_name", "building_id"])
    )
    silver: pd.DataFrame
    quar: pd.DataFrame
    extra: pd.DataFrame | None = None
    if source == "space_register":
        silver, quar, extra = transform_space(bronze_df, truth_b)
    elif source == "cafm_workorders":
        silver, quar = transform_cafm(bronze_df)
    elif source == "meter_hh_supplierA":
        silver, quar, extra = transform_meter_A(bronze_df)
    elif source == "meter_hh_supplierB":
        silver, quar, extra = transform_meter_B(bronze_df)
    elif source == "bms_trends":
        silver, quar = transform_bms(bronze_df)
    elif source == "statutory_inspections":
        silver, quar = transform_inspections(bronze_df)
    elif source == "timetable":
        silver, quar = transform_timetable(bronze_df)
    elif source == "sensors":
        silver, quar = transform_sensors(bronze_df)
    else:
        raise typer.BadParameter(f"unknown source {source}")
    sdir = root / "silver" / source
    qdir = root / "quarantine" / source
    sdir.mkdir(parents=True, exist_ok=True)
    qdir.mkdir(parents=True, exist_ok=True)
    silver.to_parquet(sdir / "silver.parquet", index=False)
    # Quarantine mixes original strings with parsed numerics/datetimes across
    # split stages; store as strings for robust inspection (silver keeps types).
    quar.astype(str).to_parquet(qdir / "quarantine.parquet", index=False)
    if extra is not None:
        try:
            extra.to_parquet(qdir / "report.parquet", index=False)
        except Exception:
            extra.astype(str).to_parquet(qdir / "report.parquet", index=False)
    return len(silver), len(quar)


@app.command(name="run-all")
def run_all(
    raw: Annotated[Path, typer.Option()] = Path("data/raw"),  # noqa: B008
    out: Annotated[Path, typer.Option()] = Path("data/lakehouse"),  # noqa: B008
    truth: Annotated[Path, typer.Option()] = Path("data/truth"),  # noqa: B008
) -> None:
    """Bronze every recognised raw file, then silver every source, then reconcile report."""
    from .bronze import sha256_file  # noqa: F401 (keep import local for CLI speed)

    root = resolve_root(out)
    patterns: dict[str, str] = {
        "space_register": "space_register_*.xlsx",
        "cafm_workorders": "cafm_workorders_*.csv",
        "meter_hh_supplierA": "meter_hh_supplierA_*.csv",
        "meter_hh_supplierB": "meter_hh_supplierB_*.csv",
        "bms_trends": "bms_trends_*.csv",
        "statutory_inspections": "statutory_inspections_*.xlsx",
        "timetable": "timetable_*.csv",
        "sensors": "sensors_*.parquet",
    }
    for source, pat in patterns.items():
        for f in sorted(raw.glob(pat)):
            dest, entry = load_bronze(source, f, root / "bronze")
            typer.echo(f"bronze {source} {f.name}: {entry['status']}")
    for source in patterns:
        _run_silver_one(source, root, truth / "buildings.parquet")
        typer.echo(f"silver {source} done")
    rep = reconcile_cmd(raw, out)
    typer.echo(json.dumps(rep, indent=2))


@app.command()
def reconcile(
    raw: Annotated[Path, typer.Option()] = Path("data/raw"),  # noqa: B008
    out: Annotated[Path, typer.Option()] = Path("data/lakehouse"),  # noqa: B008
) -> None:
    rep = reconcile_cmd(raw, out)
    typer.echo(json.dumps(rep, indent=2))


def _bronze_cell_count(bronze_df: pd.DataFrame, source: str) -> int:
    """Count wide value cells in bronze for wide→long sources."""
    if bronze_df.empty:
        return 0
    audit = {"_ingest_id", "_source_system", "_source_file", "_loaded_at", "_row_number", "_row_hash", "_sheet"}
    if source == "meter_hh_supplierB":
        hh_cols = [c for c in bronze_df.columns if c.startswith("HH")]
        return int(len(bronze_df) * len(hh_cols))
    if source == "bms_trends":
        point_cols = [
            c for c in bronze_df.columns if c not in audit and c.lower() != "timestamp" and not c.startswith("_")
        ]
        # bronze BMS has timestamp + point cols; timestamp excluded
        point_cols = [c for c in point_cols if c != "timestamp"]
        return int(len(bronze_df) * len(point_cols))
    return int(len(bronze_df))


def reconcile_cmd(raw: Path, out: Path) -> list[dict[str, object]]:
    patterns: dict[str, str] = {
        "space_register": "space_register_*.xlsx",
        "cafm_workorders": "cafm_workorders_*.csv",
        "meter_hh_supplierA": "meter_hh_supplierA_*.csv",
        "meter_hh_supplierB": "meter_hh_supplierB_*.csv",
        "bms_trends": "bms_trends_*.csv",
        "statutory_inspections": "statutory_inspections_*.xlsx",
        "timetable": "timetable_*.csv",
        "sensors": "sensors_*.parquet",
    }
    report = []
    for source, pat in patterns.items():
        raw_n = sum(raw_row_count(f, source) for f in sorted(raw.glob(pat)))
        bronze_df = _bronze_frame(out, source)
        s_path = out / "silver" / source / "silver.parquet"
        q_path = out / "quarantine" / source / "quarantine.parquet"
        s_n = len(pd.read_parquet(s_path)) if s_path.exists() else 0
        q_n = len(pd.read_parquet(q_path)) if q_path.exists() else 0
        if source in ("meter_hh_supplierB", "bms_trends"):
            # Wide→long reshape changes grain: reconcile at data-cell level.
            # Bronze data cells = wide value cells; silver+quarantine are long rows.
            bronze_cells = _bronze_cell_count(bronze_df, source)
            row = {"source": source, **reconcile_counts(raw_n, len(bronze_df), s_n, q_n)}
            row.update(
                {
                    "grain": "cell (wide→long)",
                    "bronze_cells": bronze_cells,
                    "silver_plus_q": s_n + q_n,
                    "cell_unexplained": bronze_cells - s_n - q_n,
                    "pass": bool(raw_n == len(bronze_df) and bronze_cells == s_n + q_n),
                }
            )
        else:
            row = {"source": source, **reconcile_counts(raw_n, len(bronze_df), s_n, q_n)}
        report.append(row)
    (out / "reconciliation.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


@app.command()
def catalogue(
    out: Annotated[Path, typer.Option()] = Path("platform/docs/catalogue.md"),  # noqa: B008
) -> None:
    generate_catalogue_md(out)
    typer.echo(f"wrote {out}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
