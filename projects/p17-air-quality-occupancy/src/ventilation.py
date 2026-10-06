"""P17 Ventilation adequacy analysis (CO2-based)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from .config import get_settings
from .data import load_all_co2_readings, load_all_sensor_metadata, load_spaces, load_timetable, load_readings


def _occupied_intervals(timetable: pd.DataFrame, space_id: str) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Get occupied intervals for a space from timetable (UTC timestamps)."""
    df = timetable[timetable["space_id"] == space_id].copy()
    if df.empty:
        return []
    intervals = []
    for _, row in df.iterrows():
        start = row["start_ts"]
        end = row["end_ts"]
        # Ensure UTC
        if start.tz is None:
            start = start.tz_localize("UTC")
        if end.tz is None:
            end = end.tz_localize("UTC")
        intervals.append((start, end))
    return intervals


def _resample_to_15min(df: pd.DataFrame, ts_col: str = "ts_utc", value_col: str = "value") -> pd.DataFrame:
    """Resample to regular 15-min grid per sensor."""
    if df.empty:
        return df
    df = df.copy()
    df = df.set_index(ts_col).sort_index()
    df = df.groupby("sensor_id")[value_col].resample("15min").mean().reset_index()
    return df


def _co2_rise_rate_per_occupant(
    co2_series: pd.Series,
    occ_series: pd.Series,
    window_minutes: int = 60,
) -> float | None:
    """Estimate CO2 rise rate (ppm per person per hour) from paired CO2/occupancy.
    Simple linear regression: dCO2/dt = rate * occupancy.
    """
    # Align and interpolate to 15-min grid
    co2 = co2_series.resample("15min").mean()
    occ = occ_series.resample("15min").mean()
    df = pd.DataFrame({"co2": co2, "occ": occ}).dropna()
    if len(df) < 10 or df["occ"].sum() == 0:
        return None
    # dCO2/dt
    df["dco2_dt"] = df["co2"].diff() * 4  # 15-min diff * 4 = per hour
    df = df.dropna()
    if len(df) < 5:
        return None
    # Simple OLS: dco2_dt = rate * occ
    occ_vals = df["occ"].values
    dco2 = df["dco2_dt"].values
    if occ_vals.sum() == 0:
        return None
    rate = np.sum(occ_vals * dco2) / np.sum(occ_vals**2)
    return float(rate) if rate > 0 else None


def _air_change_rate_from_decay(
    co2_series: pd.Series,
    outdoor_co2_ppm: float = 420.0,
) -> float | None:
    """Estimate air change rate (ACH) from CO2 decay after occupancy ends.
    Fits exponential decay: C(t) = C_out + (C0 - C_out) * exp(-ACH * t)
    Returns ACH (per hour) if fit is reasonable.
    """
    # Find decay segments (periods after occupancy ends)
    # Simplified: use the tail of the series when occupancy is near zero
    s = co2_series.dropna().sort_index()
    if len(s) < 20:
        return None
    # Use last 2 hours where we expect decay
    tail = s.tail(8)  # 8 periods = 2 hours at 15-min
    if len(tail) < 4:
        return None
    t = np.arange(len(tail)) * 0.25  # hours
    c = tail.values - outdoor_co2_ppm
    c = np.maximum(c, 1.0)  # avoid log(0)
    try:
        # Linear fit to log(c) = log(c0) - ACH * t
        log_c = np.log(c)
        A = np.vstack([t, np.ones_like(t)]).T
        slope, intercept = np.linalg.lstsq(A, log_c, rcond=None)[0]
        ach = -slope
        if 0.1 <= ach <= 20:  # reasonable ACH range
            return float(ach)
    except Exception:
        return None
    return None


def compute_ventilation_metrics(
    truth_dir: Path | None = None,
    co2_threshold_low: int | None = None,
    co2_threshold_high: int | None = None,
) -> pd.DataFrame:
    """Compute ventilation metrics per room with CO2 sensor.
    Returns DataFrame with one row per CO2-sensor space.
    """
    settings = get_settings()
    truth_dir = truth_dir or settings.truth_dir
    co2_threshold_low = co2_threshold_low or settings.co2_threshold_low_ppm
    co2_threshold_high = co2_threshold_high or settings.co2_threshold_high_ppm

    sensors = load_all_sensor_metadata(truth_dir)
    co2_sensors = sensors[sensors["sensor_type"] == "co2"].copy()
    if co2_sensors.empty:
        return pd.DataFrame()

    # Load all CO2 readings
    co2_readings = load_all_co2_readings(truth_dir)
    if co2_readings.empty:
        return pd.DataFrame()

    timetable = load_timetable(truth_dir)
    spaces = load_spaces(truth_dir)

    results = []
    for _, sensor in co2_sensors.iterrows():
        sensor_id = sensor["sensor_id"]
        space_id = sensor["space_id"]
        building_id = sensor["building_id"]
        space_capacity = int(spaces[spaces["space_id"] == space_id]["capacity_seats"].iloc[0]) if not spaces[spaces["space_id"] == space_id].empty else 0

        # Get CO2 readings for this sensor
        sensor_co2 = co2_readings[co2_readings["sensor_id"] == sensor_id].copy()
        if sensor_co2.empty:
            continue
        sensor_co2 = sensor_co2.set_index("ts_utc").sort_index()["value"]

        # Occupied intervals from timetable
        occupied_intervals = _occupied_intervals(timetable, space_id)

        if not occupied_intervals:
            # No timetable data — use all data as "occupied" for basic stats
            occupied_mask = pd.Series(True, index=sensor_co2.index)
            occupied_co2 = sensor_co2
            occupied_hours = len(sensor_co2) * 0.25
        else:
            # Build occupied mask
            occupied_mask = pd.Series(False, index=sensor_co2.index)
            for start, end in occupied_intervals:
                occupied_mask |= (sensor_co2.index >= start) & (sensor_co2.index < end)
            occupied_co2 = sensor_co2[occupied_mask]
            occupied_hours = len(occupied_co2) * 0.25

        total_hours = len(sensor_co2) * 0.25

        if occupied_co2.empty:
            continue

        # Metrics
        pct_above_low = (occupied_co2 > settings.co2_threshold_low_ppm).mean() * 100
        pct_above_high = (occupied_co2 > settings.co2_threshold_high_ppm).mean() * 100
        peak_co2 = float(occupied_co2.max())
        avg_co2 = float(occupied_co2.mean())

        # CO2 rise rate per occupant (if occupancy sensor exists in same space)
        meta = load_all_sensor_metadata(truth_dir)
        occ_sensors = meta[(meta["space_id"] == space_id) & (meta["sensor_type"] == "occupancy_count")]
        rise_rate = None
        if not occ_sensors.empty:
            occ_sensor_id = occ_sensors.iloc[0]["sensor_id"]
            occ_readings = load_readings(sensor_ids=[occ_sensor_id], truth_dir=truth_dir)
            if not occ_readings.empty:
                occ_series = occ_readings.set_index("ts_utc")["value"]
                rise_rate = _co2_rise_rate_per_occupant(sensor_co2, occ_series)

        # Air change rate from decay (simplified)
        ach = _air_change_rate_from_decay(sensor_co2)

        # Space metadata
        space_info = spaces[spaces["space_id"] == space_id]
        space_category = space_info["space_category"].iloc[0] if not space_info.empty else "Unknown"
        nia_m2 = float(space_info["nia_m2"].iloc[0]) if not space_info.empty else 0.0

        results.append({
            "space_id": space_id,
            "building_id": building_id,
            "space_category": space_category,
            "nia_m2": nia_m2,
            "capacity_seats": space_capacity,
            "sensor_id": sensor_id,
            "occupied_hours": occupied_hours,
            "total_hours": total_hours,
            "occupancy_pct": (occupied_hours / total_hours * 100) if total_hours > 0 else 0,
            "pct_occupied_time_above_1000ppm": round(pct_above_low, 1),
            "pct_occupied_time_above_1500ppm": round(pct_above_high, 1),
            "peak_co2_ppm": round(peak_co2, 1),
            "avg_co2_ppm": round(avg_co2, 1),
            "co2_rise_rate_ppm_per_person_per_hour": round(rise_rate, 2) if rise_rate else None,
            "estimated_ach_per_hour": round(ach, 2) if ach else None,
        })

    return pd.DataFrame(results)


def compute_ventilation_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add ventilation risk score (0-100) based on weighted metrics."""
    if df.empty:
        return df
    df = df.copy()
    # Normalize metrics to 0-1 (higher = worse)
    max_peak = df["peak_co2_ppm"].max() or 1
    max_pct_high = df["pct_occupied_time_above_1500ppm"].max() or 1
    max_pct_low = df["pct_occupied_time_above_1000ppm"].max() or 1
    min_ach = df["estimated_ach_per_hour"].min() if df["estimated_ach_per_hour"].notna().any() else 1
    max_ach = df["estimated_ach_per_hour"].max() if df["estimated_ach_per_hour"].notna().any() else 10

    df["risk_peak"] = df["peak_co2_ppm"] / max_peak
    df["risk_pct_high"] = df["pct_occupied_time_above_1500ppm"] / max_pct_high
    df["risk_pct_low"] = df["pct_occupied_time_above_1000ppm"] / max_pct_low
    df["risk_ach"] = 1 - ((df["estimated_ach_per_hour"] - min_ach) / (max_ach - min_ach + 1e-6)).clip(0, 1)

    # Weighted score
    df["ventilation_risk_score"] = (
        0.4 * df["risk_pct_high"] +
        0.3 * df["risk_peak"] +
        0.2 * df["risk_pct_low"] +
        0.1 * df["risk_ach"]
    ) * 100

    df["ventilation_risk_score"] = df["ventilation_risk_score"].round(1)
    return df