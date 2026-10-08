"""Pipeline/typology/baseline/eval tests on synthetic fixtures (no data/ dependency)."""

import numpy as np
import pandas as pd

from anomaly import baselines, detectors
from anomaly.cleaning import cleaning_report
from anomaly.evaluate import inject, score_flags
from anomaly.pipeline import run_meter
from anomaly.report import svg_series
from anomaly.typology import classify_meter, load_factors

rng = np.random.default_rng(11)


def _frame(values: np.ndarray, utility: str = "electricity") -> pd.DataFrame:
    ts = pd.date_range("2026-01-01", periods=len(values), freq="30min", tz="UTC")
    return pd.DataFrame({"ts_utc": ts, "value": values, "utility": utility})


def _weather(n: int) -> pd.DataFrame:
    ts = pd.date_range("2026-01-01", periods=n, freq="30min", tz="UTC")
    return pd.DataFrame({"ts_utc": ts, "temp_c": 5.0 + 5 * np.sin(np.arange(n) / 48)})


def test_overnight_drift_finds_creep():
    n = 2880
    hod = np.tile(np.arange(48) / 2, n // 48 + 1)[:n]
    v = np.where((hod >= 0) & (hod < 5), 4.0, 12.0) + rng.normal(0, 0.3, n)
    v[n // 2 :][(hod[n // 2 :] >= 0) & (hod[n // 2 :] < 5)] = 9.0  # creep to 75% of peak
    ts = pd.date_range("2026-01-01", periods=n, freq="30min", tz="UTC")
    assert detectors.overnight_drift(v, pd.Series(ts), peak=12.0)
    assert not detectors.overnight_drift(v[: n // 2], pd.Series(ts[: n // 2]), peak=12.0)


def test_classify_overnight_label():
    n = 960
    hod = np.tile(np.arange(48) / 2, n // 48 + 1)[:n]
    v = np.where((hod >= 0) & (hod < 5), 7.0, 12.0) + rng.normal(0, 0.3, n)
    df = _frame(v)
    labels = classify_meter(df, {}, [], peak=12.0)
    assert "high_overnight_baseload" in labels
    v2 = np.where((hod >= 0) & (hod < 5), 4.0, 12.0) + rng.normal(0, 0.3, n)
    assert "high_overnight_baseload" not in classify_meter(_frame(v2), {}, [], peak=12.0)


def test_cleaning_report_counts():
    df = pd.DataFrame({"value": [1.0, 0.0, -2.0, None, 5.0]})
    rep = cleaning_report(df)
    assert (rep["n"], rep["n_null"], rep["n_negative"], rep["n_zero"]) == (5, 1, 1, 1)


def test_regression_baseline_and_rolling_cv():
    n = 30 * 48
    ts = pd.date_range("2026-01-01", periods=n, freq="30min", tz="UTC")
    temp = 5 + 8 * np.sin(np.arange(n) / (48 * 30) * 2 * np.pi)
    df = pd.DataFrame({"ts_utc": ts, "value": 10 + 0.5 * np.maximum(0, 15.5 - temp)})
    feat = baselines.add_time_features(df, temp_col=None)
    feat["hdd"] = np.maximum(0.0, 15.5 - temp)
    model = baselines.fit_regression(feat)
    pred = baselines.predict(model, feat)
    assert baselines.cvrmse_nmbe(feat["value"].to_numpy(), pred)["cvrmse"] < 0.05
    feat["ts_utc"] = ts
    folds = baselines.rolling_origin_scores(feat, baselines.fit_regression)
    assert len(folds) >= 1 and all(f["cvrmse"] < 0.1 for f in folds)


def test_inject_deterministic_and_covering():
    base = 10 + rng.normal(0, 0.5, 3000)
    v1, t1 = inject(base, np.random.default_rng(7), n=24)
    v2, t2 = inject(base, np.random.default_rng(7), n=24)
    assert t1.equals(t2) and np.array_equal(np.nan_to_num(v1), np.nan_to_num(v2))
    assert len(t1) == 24 and set(t1["type"]) == {"step", "drift", "spike", "flatline", "ooh", "missing"}


def test_score_flags_perfect_detection():
    truth = pd.DataFrame(
        [
            {"type": "spike", "start": 100, "duration": 4, "magnitude": 5.0},
            {"type": "step", "start": 300, "duration": 50, "magnitude": 3.0},
        ]
    )
    flags = np.zeros(500, dtype=bool)
    flags[100:104] = True
    flags[302:350] = True
    scores = score_flags(flags, truth)
    assert scores["spike"]["recall"] == 1.0
    assert scores["step"]["recall"] == 1.0
    assert scores["step"]["mean_delay_periods"] == 2.0


def test_run_meter_overnight_fault_end_to_end():
    n = 60 * 48
    hod = np.tile(np.arange(48) / 2, n // 48 + 1)[:n]
    day = np.where((hod >= 8) & (hod < 18), 14.0, 2.0)
    v = 8.0 + day + rng.normal(0, 0.6, n)
    night = (hod >= 0) & (hod < 5)
    v[n // 2 :][night[n // 2 :]] = 0.60 * 24 + rng.normal(0, 0.5, int(night[n // 2 :].sum()))
    res = run_meter(_frame(v), _weather(n))
    assert "high_overnight_baseload" in res["typology"]
    assert "gradual_drift" in res["typology"]
    assert res["savings"]["gbp_year"] > 0
    assert set(res["evidence"]) == {"mad", "flat_runs", "change_points"}


def test_svg_smoke():
    ts = pd.Series(pd.date_range("2026-01-01", periods=100, freq="h", tz="UTC"))
    out = svg_series(ts, np.arange(100, dtype=float), np.zeros(100, bool), None, [50])
    assert out.startswith("<svg") and "circle" not in out and "line" in out


def test_load_factors_fallback():
    from anomaly.config import FALLBACK_FACTORS

    assert load_factors("/nonexistent/path.csv") == FALLBACK_FACTORS
