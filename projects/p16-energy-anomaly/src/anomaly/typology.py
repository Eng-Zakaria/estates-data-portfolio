"""Fault typology + savings estimation (all assumptions stated in methodology)."""

from __future__ import annotations

import numpy as np
import pandas as pd

TYPES = [
    "high_overnight_baseload",
    "weekend_operation",
    "step_change",
    "gradual_drift",
    "spike",
    "flatline_meter_fault",
    "missing_data",
]


def classify_meter(
    df: pd.DataFrame,
    flags: dict[str, np.ndarray],
    change_points: list[int],
    peak: float,
    ooh_threshold: float = 0.5,
    drift: bool = False,
) -> list[str]:
    """Rule-based typology labels for one meter's full series.

    Thresholds were set on synthetic data with a stated gap (see
    docs/methodology.md) and must be re-tuned on real meter populations:
    - ooh_threshold=0.5 separates the planted 0.6-of-peak overnight fault
      from normal baseloads (measured <= 0.47 on the small profile).
    - Overnight/weekend waste patterns apply to electricity only; night and
      weekend gas use in the heating season is legitimate heating.
    """
    labels: set[str] = set()
    utility = str(df["utility"].iloc[0]) if "utility" in df.columns else "electricity"
    hod = pd.to_datetime(df["ts_utc"], utc=True).dt.hour + pd.to_datetime(df["ts_utc"], utc=True).dt.minute / 60
    v = pd.to_numeric(df["value"], errors="coerce")
    from .detectors import overnight_ratio

    if utility == "electricity" and overnight_ratio(v, hod, peak) > ooh_threshold:
        labels.add("high_overnight_baseload")
    wknd = v[pd.to_datetime(df["ts_utc"], utc=True).dt.dayofweek >= 5].mean()
    if utility == "electricity" and np.isfinite(wknd) and peak and wknd > 0.5 * peak:
        labels.add("weekend_operation")
    if change_points:
        labels.add("step_change")
    if drift:
        labels.add("gradual_drift")
    if bool(flags.get("mad", np.zeros(1, dtype=bool)).sum() >= 3):
        labels.add("spike")
    if bool(flags.get("flatline", np.zeros(1, dtype=bool)).any()):
        labels.add("flatline_meter_fault")
    if int(df["value"].isna().sum()) > 0:
        labels.add("missing_data")
    return sorted(labels)


def load_factors(path: str = "platform/dbt/seeds/seed_emission_factors.csv") -> dict[str, float]:
    import csv

    try:
        with open(path, encoding="utf-8") as f:
            return {r["fuel"]: float(r["factor_kgco2e_per_kwh"]) for r in csv.DictReader(f)}
    except FileNotFoundError:
        from .config import FALLBACK_FACTORS

        return dict(FALLBACK_FACTORS)


def savings(
    excess_kwh_per_day: float,
    days_per_year: float = 365.0,
    tariff_gbp: float = 0.28,
    kgco2e_per_kwh: float = 0.177,
    uncertainty_pct: float = 0.25,
) -> dict[str, float]:
    """Annualised savings with a stated ±uncertainty band (residual-based default 25%)."""
    kwh = excess_kwh_per_day * days_per_year
    gbp = kwh * tariff_gbp
    co2 = kwh * kgco2e_per_kwh
    return {
        "kwh_year": round(kwh, 1),
        "gbp_year": round(gbp, 2),
        "kgco2e_year": round(co2, 1),
        "kwh_lo": round(kwh * (1 - uncertainty_pct), 1),
        "kwh_hi": round(kwh * (1 + uncertainty_pct), 1),
    }
