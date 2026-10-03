"""Typer CLI: generate / truth / snapshots."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

import typer

from .config import get_profile
from .defects import inject_defects
from .exports import (
    export_bms,
    export_cafm,
    export_inspections,
    export_meters,
    export_sensors,
    export_space_register,
    export_timetable,
)
from .generator import generate_all
from .ground_truth import write_ground_truth
from .utils import make_rng

app = typer.Typer(no_args_is_help=True)


@app.command()
def generate(
    profile: Annotated[str, typer.Option(help="small|default")] = "small",
    seed: Annotated[int, typer.Option(help="RNG seed")] = 42,
    out: Annotated[Path, typer.Option(help="raw export dir")] = Path("data/raw"),  # noqa: B008
    defects: Annotated[float, typer.Option(help="defect rate 0..1")] = 0.03,
    fmt: Annotated[str, typer.Option("--format", help="csv,xlsx,parquet (reserved)")] = "csv,xlsx,parquet",
) -> None:
    """Generate clean truth + messy source-system exports."""
    _ = fmt
    t0 = time.perf_counter()
    cfg = get_profile(profile, seed=seed, defects=defects)
    tables, gt = generate_all(cfg)
    out.mkdir(parents=True, exist_ok=True)
    truth_dir = out.parent / "truth" if out.name == "raw" else out / "truth"
    truth_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(truth_dir / f"{name}.parquet", index=False)
    rng = make_rng(seed + 999)  # separate stream for export mess so truth hashes are seed-pure
    end = cfg.end_date
    logs: list[dict[str, str]] = []
    _, lg = export_space_register(tables["spaces"], tables["buildings"], out, rng, defects, end)
    logs += lg
    _, lg = export_cafm(tables["work_orders"], out, rng, defects, end)
    logs += lg
    _, lg = export_meters(tables["meter_readings_hh"], tables["meters"], out, rng, defects, end)
    logs += lg
    _, lg = export_bms(tables["sensor_readings"], tables["sensors"], out, rng, defects, end)
    logs += lg
    _, lg = export_inspections(tables["inspections"], out, rng, defects, end)
    logs += lg
    _, lg = export_timetable(tables["timetable_events"], out, rng, defects, end)
    logs += lg
    _, lg = export_sensors(tables["sensor_readings"], out, rng, defects, end)
    logs += lg
    write_ground_truth(gt, logs, out / "ground_truth.yaml")
    dt = time.perf_counter() - t0
    typer.echo(
        f"profile={profile} seed={seed} defects={defects} tables={len(tables)} raw={out} truth={truth_dir} in {dt:.1f}s"
    )


@app.command()
def truth(
    out: Annotated[Path, typer.Option(help="ground truth yaml path")] = Path("data/raw/ground_truth.yaml"),  # noqa: B008
    profile: Annotated[str, typer.Option()] = "small",
    seed: Annotated[int, typer.Option()] = 42,
) -> None:
    """Emit planted-findings registry (no defects)."""
    cfg = get_profile(profile, seed=seed, defects=0.0)
    _, gt = generate_all(cfg)
    write_ground_truth(gt, [], out)
    typer.echo(f"wrote {out}")


@app.command()
def snapshots(
    weeks: Annotated[int, typer.Option(help="number of weekly snapshots")] = 12,
    out: Annotated[Path, typer.Option(help="snapshots dir")] = Path("data/raw_snapshots"),  # noqa: B008
    seed: Annotated[int, typer.Option()] = 42,
) -> None:
    """Weekly snapshots with decreasing defect rate (for P03 trend demo)."""
    from .config import ProfileConfig  # noqa: F401  (explicit, avoid unused lint noise)

    cfg = get_profile("small", seed=seed, defects=0.0)
    tables, _ = generate_all(cfg)
    out.mkdir(parents=True, exist_ok=True)
    base = tables["spaces"][["space_id", "building_id", "nia_m2"]].copy()
    for w in range(1, weeks + 1):
        rate = 0.12 - (w - 1) * (0.11 / max(1, weeks - 1))
        rng = make_rng(seed + w)
        wk = out / f"week_{w:02d}"
        wk.mkdir(parents=True, exist_ok=True)
        messed, logs = inject_defects(base, "spaces", rng, rate, key_col="space_id", numeric_cols=["nia_m2"])
        messed.to_parquet(wk / "spaces.parquet", index=False)
        (wk / "manifest.yaml").write_text(
            f"week: {w}\ndefect_rate: {round(rate, 4)}\nrows: {len(messed)}\n", encoding="utf-8"
        )
        _ = logs
    typer.echo(f"wrote {weeks} snapshots to {out} (defect 0.12 -> 0.01)")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
