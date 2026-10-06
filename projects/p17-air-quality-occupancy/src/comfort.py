"""P17 Thermal comfort analysis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import get_settings
from .data import load_all_temp_readings, load_all_sensor_metadata, load_spaces, load_timetable


def _occupied_intervals(timetable: pd.DataFrame, space_id: str) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Get occupied intervals for a space from timetable."""
    df = timetable[timetable["space_id"] == space_id].copy()
    if df.empty:
        return []
    intervals = []
    for _, row in df.iterrows():
        start = row["start_ts"]
        end = row["end_ts"]
        if start.tz is None:
            start = start.tz_localize("UTC")
        if end.tz is None:
            end = end.tz_localize("UTC")
        intervals.append((start, end))
    return intervals


def compute_thermal_comfort(
    truth_dir: Path | None = None,
    comfort_min_c: float | None = None,
    comfort_max_c: float | None = None,
    overheating_c: float | None = None,
) -> pd.DataFrame:
    """Compute thermal comfort metrics per room with temperature sensor."""
    settings = get_settings()
    truth_dir = truth_dir or settings.truth_dir
    comfort_min = comfort_min_c or settings.comfort_temp_min_c
    comfort_max = comfort_max_c or settings.comfort_temp_max_c
    overheating = overheating_c or settings.overheating_threshold_c

    sensors = load_all_sensor_metadata(truth_dir)
    temp_sensors = sensors[sensors["sensor_type"] == "temp"].copy()
    if temp_sensors.empty:
        return pd.DataFrame()

    temp_readings = load_all_temp_readings(truth_dir)
    if temp_readings.empty:
        return pd.DataFrame()

    timetable = load_timetable(truth_dir)
    spaces = load_spaces(truth_dir)

    results = []
    for _, sensor in temp_sensors.iterrows():
        sensor_id = sensor["sensor_id"]
        space_id = sensor["space_id"]
        building_id = sensor["building_id"]

        sensor_temp = temp_readings[temp_readings["sensor_id"] == sensor_id].copy()
        if sensor_temp.empty:
            continue
        sensor_temp = sensor_temp.set_index("ts_utc").sort_index()["value"]

        # Occupied intervals
        occupied_intervals = _occupied_intervals(timetable, space_id)

        if not occupied_intervals:
            occupied_mask = pd.Series(True, index=sensor_temp.index)
        else:
            occupied_mask = pd.Series(False, index=sensor_temp.index)
            for start, end in occupied_intervals:
                occupied_mask |= (sensor_temp.index >= start) & (sensor_temp.index < end)

        occupied_temp = sensor_temp[occupied_mask]
        total_hours = len(sensor_temp) * 0.25
        occupied_hours = len(occupied_temp) * 0.25

        if occupied_temp.empty:
            continue

        # Comfort metrics
        hours_below = ((occupied_temp < comfort_min).sum() * 0.25)
        hours_above = ((occupied_temp > comfort_max).sum() * 0.25)
        overheating_hours = ((occupied_temp > overheating).sum() * 0.25)
        total_occupied = len(occupied_temp) * 0.25

        pct_below = (hours_below / total_occupied * 100) if total_occupied > 0 else 0
        pct_above = (hours_above / total_occupied * 100) if total_occupied > 0 else 0
        pct_overheating = (overheating_hours / total_occupied * 100) if total_occupied > 0 else 0

        # Space metadata
        space_info = spaces[spaces["space_id"] == space_id]
        space_category = space_info["space_category"].iloc[0] if not space_info.empty else "Unknown"
        nia_m2 = float(space_info["nia_m2"].iloc[0]) if not space_info.empty else 0.0
        capacity = int(space_info["capacity_seats"].iloc[0]) if not space_info.empty else 0

        results.append({
            "space_id": space_id,
            "building_id": building_id,
            "space_category": space_category,
            "nia_m2": nia_m2,
            "capacity_seats": capacity,
            "sensor_id": sensor_id,
            "occupied_hours": round(occupied_hours, 1),
            "total_hours": round(total_hours, 1),
            "occupancy_pct": round(occupied_hours / total_hours * 100, 1) if total_hours > 0 else 0,
            "avg_temp_c": round(float(occupied_temp.mean()), 1),
            "min_temp_c": round(float(occupied_temp.min()), 1),
            "max_temp_c": round(float(occupied_temp.max()), 1),
            "hours_below_comfort": round(hours_below, 1),
            "hours_above_comfort": round(hours_above, 1),
            "overheating_hours": round(overheating_hours, 1),
            "pct_time_below_comfort": round(pct_below, 1),
            "pct_time_above_comfort": round(pct_above, 1),
            "pct_overheating_time": round(pct_overheating, 1),
        })

    return pd.DataFrame(results)


def compute_comfort_risk_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add comfort risk score (0-100) based on weighted metrics."""
    if df.empty:
        return df
    df = df.copy()
    # Higher score = worse comfort
    max_below = df["hours_below_comfort"].max() or 1
    max_above = df["hours_above_comfort"].max() or 1
    max_overheat = df["overheating_hours"].max() or 1

    df["risk_below"] = df["hours_below_comfort"] / max_below
    df["risk_above"] = df["hours_above_comfort"] / max_above
    df["risk_overheat"] = df["overheating_hours"] / max_overheat

    df["comfort_risk_score"] = (
        0.4 * df["risk_overheat"] +
        0.3 * df["risk_above"] +
        0.3 * df["risk_below"]
    ) * 100

    df["comfort_risk_score"] = df["comfort_risk_score"].round(1)
    return df