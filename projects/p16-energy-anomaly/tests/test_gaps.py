"""Tests for real-world gaps: BDG2 meters with missing readings or weather.

These fixtures came out of the BDG2 review run, where several meters hit
ValueErrors inside sklearn (NaN features / NaN targets) and one had no finite
reading at all. Each case is now pinned so it cannot come back.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from anomaly.cleaning import winsorise_fit
from anomaly.pipeline import run_meter


def _frame(values: np.ndarray, freq: str = "30min") -> pd.DataFrame:
    ts = pd.date_range("2026-01-01", periods=len(values), freq=freq, tz="UTC")
    return pd.DataFrame({"ts_utc": ts, "value": values, "utility": "electricity"})


def _weather(n: int, temp: float | None = 5.0, freq: str = "30min") -> pd.DataFrame:
    ts = pd.date_range("2026-01-01", periods=n, freq=freq, tz="UTC")
    return pd.DataFrame({"ts_utc": ts, "temp_c": temp if temp is not None else np.nan})


def _clean(n: int = 1200, rng: np.random.Generator | None = None) -> np.ndarray:
    r = rng or np.random.default_rng(3)
    hod = np.tile(np.arange(48) / 2, n // 48 + 1)[:n]
    return np.where((hod >= 8) & (hod < 18), 12.0, 2.0) + r.normal(0, 0.4, n)


def test_all_missing_meter_returns_data_quality_only() -> None:
    values = np.full(200, np.nan)
    res = run_meter(_frame(values), _weather(200))
    assert res["typology"] == ["missing_data"]
    assert res["peak"] == 0.0
    assert res["savings"]["gbp_year"] == 0.0
    assert res["n_flags"]["missing"] == 200


def test_meter_with_gaps_in_series_still_analysed() -> None:
    rng = np.random.default_rng(4)
    v = _clean(1200, rng)
    v[300:340] = np.nan  # a real comms outage mid-series
    res = run_meter(_frame(v), _weather(1200))
    assert res["peak"] > 0
    assert "missing_data" in res["typology"]
    assert res["savings"]["gbp_year"] >= 0.0


def test_missing_weather_does_not_break_baselines() -> None:
    # BDG2 site weather is not gap-free: NaN temp_c must not reach Ridge/GBM
    v = _clean(1200)
    res = run_meter(_frame(v), _weather(1200, temp=None))
    assert set(res["cv"]) == {"median_profile", "regression", "gbm"}
    assert all(np.isfinite(r["cvrmse"]) for r in res["cv"].values())


def test_training_window_entirely_missing_still_fits() -> None:
    # First 28 days (the baseline training window) have no readings; the
    # pipeline must fall back to any finite period rather than crash.
    v = _clean(1600)
    v[: 28 * 48] = np.nan
    res = run_meter(_frame(v), _weather(1600))
    assert res["peak"] > 0
    assert all(np.isfinite(r["cvrmse"]) for r in res["cv"].values())


def test_hourly_bdg2_cadence_runs() -> None:
    ts = pd.date_range("2017-01-01", periods=2000, freq="h", tz="UTC")
    v = np.where(((ts.hour >= 8) & (ts.hour < 18)), 9.0, 1.5) + np.random.default_rng(5).normal(0, 0.3, 2000)
    df = pd.DataFrame({"ts_utc": ts, "value": v, "utility": "electricity"})
    res = run_meter(df, _weather(2000, temp=12.0, freq="h"))
    assert res["peak"] > 0
    assert "high_overnight_baseload" not in res["typology"]


def test_winsorise_fit_handles_no_finite_values() -> None:
    out = winsorise_fit(np.array([np.nan, np.nan]))
    assert np.isnan(out).all()
    single = winsorise_fit(np.array([5.0]))
    assert single.tolist() == [5.0]
