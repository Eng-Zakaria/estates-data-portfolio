"""CLI: fetch-bdg2 / run-campus / evaluate / review-bdg2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

app = typer.Typer(no_args_is_help=True)

FINDING_DETECTOR = {
    "high_overnight_baseload": ("overnight_rule", "mad"),
    "weekend_operation": ("weekend_rule", None),
    "step_change": ("mean_shift_scan", None),
    "gradual_drift": ("overnight_drift", None),
    "spike": ("mad_zscore", "mad"),
    "flatline_meter_fault": ("flatline", "flatline"),
    "missing_data": ("cleaning", None),
}


def _findings_for(res: dict[str, Any]) -> list[dict[str, Any]]:
    first = res.get("first_flags", {})
    assert isinstance(first, dict)
    cps = res.get("change_points", [])
    assert isinstance(cps, list)
    out = []
    for t in res["typology"]:
        detector, flag_key = FINDING_DETECTOR.get(t, ("ensemble", None))
        start = ""
        if t == "step_change" and cps:
            start = str(cps[0])
        elif flag_key is not None and first.get(flag_key):
            start = str(first[flag_key])
        out.append(
            {
                "type": t,
                "detector": detector,
                "start": start,
                "kwh_day": res["attributed_excess_kwh_day"],
                "cost_year": res["savings"]["gbp_year"],
                "kgco2e_year": res["savings"]["kgco2e_year"],
            }
        )
    return out


def _plot_for(df: Any, res: dict[str, Any]) -> str:
    import numpy as np
    import pandas as pd

    from .report import svg_series

    d = df.sort_values("ts_utc").reset_index(drop=True)
    v = pd.to_numeric(d["value"], errors="coerce").to_numpy(float)
    n = len(v)
    ev = res.get("evidence", {})
    assert isinstance(ev, dict)
    mad_on = np.zeros(n, dtype=bool)
    for i in ev.get("mad", []):
        if 0 <= int(i) < n:
            mad_on[int(i)] = True
    flat_on = np.zeros(n, dtype=bool)
    for run in ev.get("flat_runs", []):
        flat_on[max(0, run[0]) : min(n, run[1] + 1)] = True
    cps_idx = [int(i) for i in ev.get("change_points", []) if 0 <= int(i) < n]
    ts = pd.to_datetime(d["ts_utc"], utc=True)
    return svg_series(ts, v, mad_on, flat_on, sorted(set(cps_idx)))


@app.command()
def fetch_bdg2() -> None:
    from .data_bdg2 import download_zip, extract_subset

    out = extract_subset(download_zip())
    typer.echo(f"bdg2 subset -> {out}")


@app.command()
def run_campus(
    out: Annotated[Path, typer.Option()] = Path("projects/p16-energy-anomaly/outputs"),  # noqa: B008
) -> None:
    """Action list over all small-profile meters + default-cache planted meters."""

    from .data_campus import DEFAULT_CACHE, load_campus
    from .pipeline import run_meter
    from .report import building_page, write_anomalies, write_scorecard

    df, weather = load_campus()
    try:
        dfd, wd = load_campus(truth_dir=DEFAULT_CACHE)
        extra = [(m, dfd[dfd.meter_id == m], wd) for m in ("M-B019-G01", "M-B015-E01")]
    except FileNotFoundError:
        extra = []
    jobs: list[tuple[str, Any, Any, str]] = [
        (str(mid), grp, weather, "small") for mid, grp in df.groupby("meter_id")
    ] + [(m, g, w, "default-cache") for m, g, w in extra]
    rows: list[dict[str, Any]] = []
    score: list[dict[str, Any]] = []
    for mid, grp, wx, src in jobs:
        res: dict[str, Any] = run_meter(grp, wx)  # type: ignore[assignment]
        bid = str(grp["building_id"].iloc[0])
        findings = _findings_for(res)
        notes = (
            f"source={src}; peak={res['peak']:.1f} kWh/period; flags={res['n_flags']}; "
            f"attributed excess={res['attributed_excess_kwh_day']} kWh/day "
            f"(overnight={res['overnight_excess_kwh_day']}, residual={res['residual_excess_kwh_day']})"
        )
        building_page(bid, findings, _plot_for(grp, res), notes, out / "reports" / f"{bid}.html")
        rows.append({"meter_id": mid, "building": bid, "source": src, **res["savings"]})
        score.append(
            {
                "building": bid,
                "meter_id": mid,
                "source": src,
                "peak": res["peak"],
                "types": ",".join(res["typology"]),
                "kwh_year": res["savings"]["kwh_year"],
                "gbp_year": res["savings"]["gbp_year"],
            }
        )
    score.sort(key=lambda r: -r["gbp_year"])
    write_anomalies(rows, out / "anomalies.parquet")
    write_scorecard(score, out / "building_scorecard.parquet")
    (out / "action_list.json").write_text(json.dumps(score, indent=2), encoding="utf-8")
    typer.echo(f"wrote {len(rows)} anomaly rows + scorecard -> {out}")
    for s in score[:5]:
        typer.echo(f"  {s['meter_id']} £{s['gbp_year']} [{s['types']}]")


@app.command()
def evaluate(
    out: Annotated[Path, typer.Option()] = Path("projects/p16-energy-anomaly/outputs"),  # noqa: B008
    seed: Annotated[int, typer.Option()] = 7,
) -> None:
    """Full eval: injection study + campus action list. Writes metrics.json (README source of truth)."""
    import numpy as np

    from .baselines import apply_median_profile, baseline_median_profile
    from .data_campus import load_campus
    from .evaluate import inject, run_detectors, score_flags

    rng = np.random.default_rng(seed)
    # Injection study runs on the default-profile cache (24 months, so 210+
    # sparse injections fit without overlap). Generated on demand so `make
    # eval` reproduces from a clean clone (see scripts/gen_default_cache).
    from .data_campus import DEFAULT_CACHE

    if not (DEFAULT_CACHE / "meter_readings_hh.parquet").exists():
        import sys as _sys
        from pathlib import Path as _Path

        _sys.path.insert(0, str(_Path("projects/p16-energy-anomaly/scripts")))
        from gen_default_cache import main as gen_default

        gen_default()
    df, _ = load_campus(truth_dir=DEFAULT_CACHE)
    mid = "M-B001-E01"
    series = df[df.meter_id == mid].sort_values("ts_utc").reset_index(drop=True)
    hold = series.copy()
    base = hold["value"].to_numpy(float)
    # sparse non-overlapping injections after a clean 90-day training window;
    # the baseline is fit on uncorrupted history (M&V practice)
    corrupted, truth = inject(base, rng, n=210, protect_head=90 * 48)
    hold_c = hold.copy()
    hold_c["value"] = corrupted
    prof = baseline_median_profile(hold_c.iloc[: 90 * 48])
    residual = hold_c["value"].to_numpy(float) - apply_median_profile(hold_c, prof)
    methods = run_detectors(hold_c[["ts_utc", "value"]], residual, seed=seed)
    scores = {name: score_flags(fl, truth) for name, fl in methods.items()}
    # action list via run_campus, then read back the ranking
    run_campus(out)
    board = json.loads((out / "action_list.json").read_text(encoding="utf-8"))
    metrics = {
        "injection_scores": scores,
        "injection_n": int(len(truth)),
        "held_out_meter": mid,
        "seed": seed,
        "action_list_top5": board[:5],
    }
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    typer.echo(f"wrote {out / 'metrics.json'}")


@app.command()
def review_bdg2(
    out: Annotated[Path, typer.Option()] = Path("projects/p16-energy-anomaly/outputs/bdg2"),  # noqa: B008
    tariff_usd: Annotated[float, typer.Option()] = 0.15,
) -> None:
    """Heuristic-flag review pack over all 50 BDG2 subset buildings.

    No labels exist, so NO accuracy is claimed: the top-6 by flag count get
    evidence pages for manual review. Tariff is an illustrative US commercial
    $/kWh; no CO2 is reported (UK DESNZ factors do not apply to US/IE grids).
    """

    from .data_bdg2 import load_bdg2_subset
    from .pipeline import run_meter
    from .report import building_page

    readings, weather = load_bdg2_subset()
    ranked = []
    cache: dict[str, Any] = {}
    for b, grp in readings.groupby("building"):
        site = str(grp["site"].iloc[0])
        wx = weather[weather.site == site][["ts_utc", "temp_c"]]
        g = grp.rename(columns={"value": "value"})[["ts_utc", "value"]].copy()
        g["utility"] = "electricity"
        res: dict[str, Any] = run_meter(g, wx, tariff=tariff_usd, seed=7)  # type: ignore[assignment]
        total_flags = sum(v for k, v in res["n_flags"].items() if k != "drift") + 1000 * int(res["drift"])
        ranked.append((total_flags, b, site, res))
        cache[b] = (grp, res)
    ranked.sort(key=lambda r: -r[0])
    out.mkdir(parents=True, exist_ok=True)
    review = []
    for total, b, site, res in ranked[:6]:
        grp, _ = cache[b]
        findings = _findings_for(res)
        notes = (
            f"BDG2 {b} site={site}; no labels, manual review only; "
            f"costs in USD at illustrative ${tariff_usd}/kWh; no CO2 reported "
            f"(UK factors do not apply); peak={res['peak']:.1f} kWh/h; flags={res['n_flags']}"
        )
        building_page(f"BDG2-{b}", findings, _plot_for(grp, res), notes, out / f"{b}.html", currency="$")
        review.append(
            {
                "building": b,
                "site": site,
                "total_flags": int(total),
                "types": ",".join(res["typology"]),
                "kwh_year": res["savings"]["kwh_year"],
                "usd_year_illustrative": round(res["savings"]["kwh_year"] * tariff_usd, 2),
            }
        )
    (out / "review.json").write_text(json.dumps(review, indent=2), encoding="utf-8")
    typer.echo(f"reviewed {len(ranked)} buildings, top-6 pack -> {out}")
    for r in review:
        typer.echo(f"  {r['building']} flags={r['total_flags']} [{r['types']}]")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
