"""Detector unit tests on synthetic series with known answers (fast, seeded)."""

import numpy as np
import pandas as pd

from anomaly import detectors
from anomaly.cleaning import flag_flatline, winsorise_fit
from anomaly.typology import savings

rng = np.random.default_rng(7)


def _series(n: int = 500, base: float = 10.0, noise: float = 0.5) -> np.ndarray:
    return base + rng.normal(0, noise, n)


def test_mad_finds_spike():
    v = _series()
    v[250] += 30
    flags = detectors.mad_zscore(v - np.median(v))
    assert flags[250]
    assert flags.sum() < 10


def test_mad_clean_series_quiet():
    assert detectors.mad_zscore(_series()).sum() == 0


def test_cusum_finds_sustained_shift_and_delay():
    v = _series(600)
    v[300:] += 4.0
    flags = detectors.cusum_flags(v - np.median(v[:300]))
    first = int(np.argmax(flags))
    assert flags[300:].any()
    assert 300 <= first < 360  # detection delay bounded


def test_cusum_clean_quiet():
    assert detectors.cusum_flags(_series() - 10.0).sum() == 0


def test_mean_shift_scan_locates_step():
    v = _series(600)
    v[300:] += 6.0
    hits = detectors.mean_shift_scan(v)
    assert any(abs(h - 300) <= 48 for h in hits)


def test_mean_shift_scan_clean_empty():
    assert detectors.mean_shift_scan(_series()) == []


def test_isolation_forest_flags_spike():
    v = _series(400)
    v[100] += 40
    df = pd.DataFrame({"ts_utc": pd.date_range("2026-01-01", periods=400, freq="30min", tz="UTC")})
    flags = detectors.isolation_forest_flags(df, v - np.median(v), seed=7, contamination=0.02)
    assert flags[100]


def test_flatline_detector():
    v = _series(200)
    v[100:160] = v[100]
    assert flag_flatline(pd.Series(v)).iloc[150]


def test_winsorise_clips_only_fit():
    v = np.array([1.0, 2.0, 3.0, 100.0])
    assert winsorise_fit(v).max() < 100.0


def test_savings_math():
    s = savings(10.0, days_per_year=100.0, tariff_gbp=0.5, kgco2e_per_kwh=0.2, uncertainty_pct=0.1)
    assert s["kwh_year"] == 1000.0
    assert s["gbp_year"] == 500.0
    assert s["kgco2e_year"] == 200.0
    assert s["kwh_lo"] == 900.0 and s["kwh_hi"] == 1100.0
