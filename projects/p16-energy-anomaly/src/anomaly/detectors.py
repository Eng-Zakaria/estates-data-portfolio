"""Anomaly detectors on residuals/series (all deterministic given seeds).

- mad_zscore: robust residual z (median/MAD), flags |z| > threshold.
- isolation_forest: sklearn IsolationForest on [hour_sin, hour_cos, dow, value, residual].
- cusum: two-sided tabular CUSUM on residuals for sustained shifts.
- mean_shift_scan: sliding two-window mean comparison (change-point scan).
- overnight_rule: overnight (00-05) mean above threshold_pct of daily peak.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest


def mad_zscore(residual: np.ndarray, threshold: float = 4.0) -> np.ndarray:
    r = np.asarray(residual, float)
    med = np.median(r[np.isfinite(r)])
    mad = np.median(np.abs(r[np.isfinite(r)] - med)) or 1e-9
    z = 0.6745 * (r - med) / mad
    out = np.abs(z) > threshold
    return np.where(np.isfinite(r), out, False)


def isolation_forest_flags(
    df: pd.DataFrame, residual: np.ndarray, seed: int = 7, contamination: float = 0.02
) -> np.ndarray:
    t = pd.to_datetime(df["ts_utc"], utc=True)
    hour = t.dt.hour + t.dt.minute / 60.0
    X = np.column_stack(
        [
            np.sin(2 * np.pi * hour / 24),
            np.cos(2 * np.pi * hour / 24),
            t.dt.dayofweek.to_numpy(),
            np.asarray(residual, float),
        ]
    )
    X = np.nan_to_num(X, nan=0.0)
    pred = IsolationForest(contamination=contamination, random_state=seed).fit_predict(X)
    return pred == -1


def cusum_flags(residual: np.ndarray, drift: float = 1.0, threshold: float = 8.0, ref_frac: float = 0.25) -> np.ndarray:
    """Two-sided CUSUM on standardised residuals; flags runs where cumulative sum exceeds threshold.

    The in-control reference (median + MAD-based sd) comes from the leading
    `ref_frac` of the series, not the whole series: a sustained shift occupying
    a large share of the window would otherwise drag a global median/sd toward
    itself and mute detection. NaNs reset the accumulators.
    """
    r = np.asarray(residual, float)
    n = len(r)
    k = max(48, int(n * ref_frac))
    ref = r[:k][np.isfinite(r[:k])]
    if len(ref) < 8:
        ref = r[np.isfinite(r)]
    med = float(np.median(ref))
    mad = float(np.median(np.abs(ref - med))) or 1e-9
    sd = 1.4826 * mad
    z = (r - med) / sd
    pos = neg = 0.0
    flags = np.zeros(len(r), dtype=bool)
    for i, v in enumerate(z):
        if not np.isfinite(v):
            pos = neg = 0.0
            continue
        pos = max(0.0, pos + v - drift)
        neg = min(0.0, neg + v + drift)
        if pos > threshold or neg < -threshold:
            flags[i] = True
    return flags


def mean_shift_scan(values: np.ndarray, window: int = 48, min_gap: float = 0.0, threshold_z: float = 6.0) -> list[int]:
    """Return centre indices where trailing/leading window means differ by > threshold robust z."""
    v = np.asarray(values, float)
    med = np.median(v[np.isfinite(v)])
    mad = np.median(np.abs(v[np.isfinite(v)] - med)) or 1e-9
    hits: list[int] = []
    for i in range(window, len(v) - window):
        a = v[i - window : i]
        b = v[i : i + window]
        if np.isfinite(a).sum() < window // 2 or np.isfinite(b).sum() < window // 2:
            continue
        gap = abs(np.nanmean(b) - np.nanmean(a))
        if gap > max(min_gap, threshold_z * (mad / 0.6745) * np.sqrt(2.0) / np.sqrt(window)):
            hits.append(i)
    # non-max suppression: keep first of each clustered run
    kept: list[int] = []
    for h in hits:
        if not kept or h - kept[-1] > window:
            kept.append(h)
    return kept


def overnight_drift(
    values: np.ndarray,
    ts_utc: pd.Series,
    peak: float,
    window: int = 1344,
    threshold_frac: float = 0.08,
    threshold_z: float = 6.0,
) -> bool:
    """True when mean overnight (00-05) use in the last `window` periods exceeds
    the first `window` by more than `threshold_frac` of peak (and significantly).

    Baseload-creep test that needs no fitted baseline: nights are free of
    occupancy noise, so a rising night mean is a rising baseload. Electricity
    only (night gas use is seasonal heating). Threshold 0.08 sits in the
    measured synthetic gap (normals <= 0.006, planted 0.6-of-peak fault >= 0.12);
    re-tune on real meter populations.
    """
    v = np.asarray(pd.to_numeric(pd.Series(values), errors="coerce"), float)
    hod = pd.to_datetime(ts_utc, utc=True).dt.hour.to_numpy()
    n = len(v)
    w = max(48, min(window, n // 4))
    if n < 2 * w or not peak:
        return False
    night = (hod >= 0) & (hod < 5)
    a = v[:w][night[:w]]
    b = v[n - w :][night[n - w :]]
    a = a[np.isfinite(a)]
    b = b[np.isfinite(b)]
    if len(a) < 24 or len(b) < 24:
        return False
    diff = float(np.mean(b)) - float(np.mean(a))
    se = float(np.std(np.concatenate([a, b]))) / np.sqrt(min(len(a), len(b))) or 1e-9
    return bool(diff / peak > threshold_frac and diff / se > threshold_z)


def overnight_ratio(values: pd.Series, hod: pd.Series, peak: float) -> float:
    night = values[(hod >= 0) & (hod < 5)].mean()
    return float(night / peak) if peak else 0.0
