"""P17 Sensor health analysis (dropouts, stuck values, drift)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import get_settings
from .data import load_all_sensor_metadata, load_readings


def _detect_stuck_values(
    series: pd.Series,
    window: int,
    tolerance: float = 1e-6,
) -> int:
    """Count periods where value is stuck (same value for >= window consecutive periods)."""
    if len(series) < window:
        return 0
    diff = series.diff().abs()
    stuck = (diff < tolerance).astype(int)
    # Rolling sum of consecutive stuck periods
    stuck_rolling = stuck.rolling(window=window, min_periods=window).sum()
    return int((stuck_rolling >= window).sum())


def _detect_dropouts(
    series: pd.Series,
    max_gap_periods: int = 4,
    expected_freq: str = "15min",
) -> int:
    """Count dropout periods (gaps longer than expected)."""
    if len(series) < 2:
        return 0
    # Expected regular grid
    expected = pd.date_range(series.index.min(), series.index.max(), freq=expected_freq, tz="UTC")
    actual = series.index
    # Count missing expected timestamps
    missing = expected.difference(actual)
    # Group consecutive missing into gap events
    if len(missing) == 0:
        return 0
    gap_starts = missing[~missing.isin(missing - pd.Timedelta(minutes=15))]
    # Count gaps longer than max_gap_periods
    gap_lengths = []
    for gs in gap_starts:
        gap_end = gs
        while gap_end + pd.Timedelta(minutes=15) in missing:
            gap_end += pd.Timedelta(minutes=15)
        gap_len = len(missing[(missing >= gs) & (missing <= gap_end)])
        gap_lengths.append(gap_len)
    return int(sum(1 for gl in gap_lengths if gl > max_gap_periods))


def _detect_drift(
    series: pd.Series,
    window_days: int = 14,
    percentile: float = 0.01,
) -> dict | None:
    """Detect upward drift in low-percentile values (e.g., 1st percentile CO2 trending up).
    Returns drift info if significant trend found.
    """
    if len(series) < window_days * 96:  # 96 periods/day at 15-min
        return None

    # Resample to daily 1st percentile
    daily_p1 = series.resample("1D").quantile(percentile).dropna()
    if len(daily_p1) < window_days // 2:
        return None

    # Linear trend on daily 1st percentile
    x = np.arange(len(daily_p1))
    y = daily_p1.values
    try:
        A = np.vstack([x, np.ones_like(x)]).T
        slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
        # Annualized drift (ppm/year)
        drift_per_year = slope * 365
        # Significance: R^2
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        if abs(drift_per_year) > 50 and r2 > 0.3:  # meaningful drift threshold
            return {
                "drift_ppm_per_year": round(float(drift_per_year), 1),
                "r2": round(float(r2), 3),
                "trend_start_ppm": round(float(daily_p1.iloc[0]), 1),
                "trend_end_ppm": round(float(daily_p1.iloc[-1]), 1),
            }
    except Exception:
        return None
    return None


def compute_sensor_health(
    truth_dir: Path | None = None,
    sensor_types: list[str] | None = None,
    stuck_window: int | None = None,
    dropout_max_gap: int | None = None,
    drift_window_days: int | None = None,
    drift_percentile: float | None = None,
) -> pd.DataFrame:
    """Compute sensor health metrics for all sensors."""
    settings = get_settings()
    truth_dir = truth_dir or settings.truth_dir

    stuck_window = stuck_window or settings.stuck_value_window
    dropout_max_gap = dropout_max_gap or settings.dropout_max_gap_periods
    drift_window_days = drift_window_days or settings.drift_window_days
    drift_percentile = drift_percentile or settings.drift_percentile

    sensors = load_all_sensor_metadata(truth_dir)
    if sensors.empty:
        return pd.DataFrame()

    if sensor_types:
        sensors = sensors[sensors["sensor_type"].isin(sensor_types)]

    results = []
    for _, sensor in sensors.iterrows():
        sensor_id = sensor["sensor_id"]
        space_id = sensor["space_id"]
        building_id = sensor["building_id"]
        sensor_type = sensor["sensor_type"]
        install_date = sensor["install_date"]

        # Load readings for this sensor
        df = load_readings(sensor_ids=[sensor_id], truth_dir=truth_dir)
        if df.empty:
            results.append({
                "sensor_id": sensor_id,
                "space_id": space_id,
                "building_id": building_id,
                "sensor_type": sensor_type,
                "install_date": install_date,
                "total_readings": 0,
                "date_range_start": None,
                "date_range_end": None,
                "stuck_periods": 0,
                "dropout_events": 0,
                "drift_detected": False,
                "drift_ppm_per_year": None,
                "drift_r2": None,
                "health_score": 0,
            })
            continue

        df = df.set_index("ts_utc").sort_index()["value"]
        total_readings = len(df)

        # Stuck values
        stuck_count = _detect_stuck_values(df, stuck_window)

        # Dropouts
        dropout_count = _detect_dropouts(df, dropout_max_gap)

        # Drift (only for CO2)
        drift_info = None
        if sensor_type == "co2":
            drift_info = _detect_drift(df, drift_window_days, drift_percentile)

        drift_detected = drift_info is not None

        # Health score (0-100, higher = healthier)
        # Penalize stuck, dropouts, drift
        stuck_penalty = min(stuck_count / 10, 0.3)
        dropout_penalty = min(dropout_count / 5, 0.3)
        drift_penalty = 0.4 if drift_detected else 0
        health_score = max(0, 100 * (1 - stuck_penalty - dropout_penalty - drift_penalty))

        results.append({
            "sensor_id": sensor_id,
            "space_id": sensor["space_id"],
            "building_id": building_id,
            "sensor_type": sensor_type,
            "install_date": install_date,
            "total_readings": total_readings,
            "date_range_start": df.index.min(),
            "date_range_end": df.index.max(),
            "stuck_periods": stuck_count,
            "dropout_events": dropout_count,
            "drift_detected": drift_detected,
            "drift_ppm_per_year": drift_info["drift_ppm_per_year"] if drift_info else None,
            "drift_r2": drift_info["r2"] if drift_info else None,
            "health_score": round(health_score, 1),
        })

    return pd.DataFrame(results)