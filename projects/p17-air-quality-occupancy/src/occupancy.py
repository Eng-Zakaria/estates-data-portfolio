"""P17 Occupancy analysis (actual vs timetabled)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import get_settings
from .data import load_all_occupancy_readings, load_all_sensor_metadata, load_spaces, load_timetable


def _occupied_intervals(timetable: pd.DataFrame, space_id: str) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
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


def compute_occupancy_analysis(
    truth_dir: Path | None = None,
    no_show_threshold_min: int | None = None,
    overcapacity_tolerance: float | None = None,
) -> pd.DataFrame:
    """Compute actual vs timetabled occupancy metrics per room."""
    settings = get_settings()
    truth_dir = truth_dir or settings.truth_dir
    no_show_thresh = no_show_threshold_min or settings.no_show_threshold_min
    overcap_tol = overcapacity_tolerance or settings.overcapacity_tolerance

    sensors = load_all_sensor_metadata(truth_dir)
    occ_sensors = sensors[sensors["sensor_type"] == "occupancy_count"].copy()
    if occ_sensors.empty:
        return pd.DataFrame()

    occ_readings = load_all_occupancy_readings(truth_dir)
    if occ_readings.empty:
        return pd.DataFrame()

    timetable = load_timetable(truth_dir)
    spaces = load_spaces(truth_dir)

    results = []
    for _, sensor in occ_sensors.iterrows():
        sensor_id = sensor["sensor_id"]
        space_id = sensor["space_id"]
        building_id = sensor["building_id"]

        # Get occupancy readings
        sensor_occ = occ_readings[occ_readings["sensor_id"] == sensor_id].copy()
        if sensor_occ.empty:
            continue
        sensor_occ = sensor_occ.set_index("ts_utc").sort_index()["value"]

        # Timetable events for this space
        space_tt = timetable[timetable["space_id"] == space_id].copy()
        if space_tt.empty:
            # No timetable — only actual occupancy
            continue

        space_info = spaces[spaces["space_id"] == space_id]
        space_category = space_info["space_category"].iloc[0] if not space_info.empty else "Unknown"
        nia_m2 = float(space_info["nia_m2"].iloc[0]) if not space_info.empty else 0.0
        capacity = int(space_info["capacity_seats"].iloc[0]) if not space_info.empty else 0

        # Process each timetable event
        event_results = []
        for _, event in space_tt.iterrows():
            event_id = event["event_id"]
            start = event["start_ts"]
            end = event["end_ts"]
            if start.tz is None:
                start = start.tz_localize("UTC")
            if end.tz is None:
                end = end.tz_localize("UTC")
            duration_hours = (end - start).total_seconds() / 3600

            group_size = int(event["group_size"])
            module_code = event["module_code"]

            # Actual occupancy during event window
            event_occ = sensor_occ[(sensor_occ.index >= start) & (sensor_occ.index < end)]
            if event_occ.empty:
                actual_avg = 0
                actual_max = 0
                actual_min = 0
                no_show = True
            else:
                actual_avg = float(event_occ.mean())
                actual_max = float(event_occ.max())
                actual_min = float(event_occ.min())
                # No-show: max occupancy < threshold for first N minutes
                early_window = event_occ[(event_occ.index >= start) & (event_occ.index < start + pd.Timedelta(minutes=no_show_thresh))]
                early_max = float(early_window.max()) if not early_window.empty else 0
                no_show = early_max == 0

            # Over-capacity
            over_capacity = actual_max > capacity * overcap_tol

            event_results.append({
                "event_id": event_id,
                "duration_hours": duration_hours,
                "group_size": group_size,
                "module_code": module_code,
                "actual_avg_occupancy": round(actual_avg, 1),
                "actual_max_occupancy": round(actual_max, 1),
                "actual_min_occupancy": round(actual_min, 1),
                "no_show": no_show,
                "over_capacity": over_capacity,
            })

        if not event_results:
            continue

        # Aggregate per space
        event_df = pd.DataFrame(event_results)
        total_events = len(event_df)
        no_show_count = int(event_df["no_show"].sum())
        overcap_count = int(event_df["over_capacity"].sum())
        no_show_rate = no_show_count / total_events * 100
        overcap_rate = overcap_count / total_events * 100

        # Utilization metrics
        avg_actual = event_df["actual_avg_occupancy"].mean()
        max_actual = event_df["actual_max_occupancy"].max()
        avg_group = event_df["group_size"].mean()

        space_info = spaces[spaces["space_id"] == space_id]
        space_capacity = int(space_info["capacity_seats"].iloc[0]) if not space_info.empty else 0

        results.append({
            "space_id": space_id,
            "building_id": building_id,
            "space_category": space_category,
            "nia_m2": nia_m2,
            "capacity_seats": space_capacity,
            "sensor_id": sensor_id,
            "total_events": total_events,
            "no_show_count": no_show_count,
            "no_show_rate_pct": round(no_show_rate, 1),
            "overcapacity_count": overcap_count,
            "overcapacity_rate_pct": round(overcap_rate, 1),
            "avg_actual_occupancy": round(avg_actual, 1),
            "max_actual_occupancy": round(max_actual, 1),
            "avg_group_size": round(avg_group, 1),
            "utilization_rate_pct": round(avg_actual / space_capacity * 100, 1) if space_capacity > 0 else 0,
        })

    return pd.DataFrame(results)


def compute_occupancy_utilization_score(df: pd.DataFrame) -> pd.DataFrame:
    """Add utilization risk score (high = poorly utilized)."""
    if df.empty:
        return df
    df = df.copy()
    # High score = underutilized (low utilization) OR over-utilized (high overcapacity)
    max_util = df["utilization_rate_pct"].max() or 100
    max_no_show = df["no_show_rate_pct"].max() or 100
    max_overcap = df["overcapacity_rate_pct"].max() or 100

    # Invert: low utilization and high no-show are both bad
    df["risk_underutilized"] = 1 - (df["utilization_rate_pct"] / max_util)
    df["risk_no_show"] = df["no_show_rate_pct"] / max_no_show
    df["risk_overcap"] = df["overcapacity_rate_pct"] / max_overcap

    df["utilization_risk_score"] = (
        0.5 * df["risk_underutilized"] +
        0.3 * df["risk_no_show"] +
        0.2 * df["risk_overcap"]
    ) * 100

    df["utilization_risk_score"] = df["utilization_risk_score"].round(1)
    return df


def compute_observed_occupancy_fact(
    truth_dir: Path | None = None,
) -> pd.DataFrame:
    """Produce fct_space_observed_occupancy for P06 integration."""
    settings = get_settings()
    truth_dir = truth_dir or settings.truth_dir

    occ_sensors = load_all_sensor_metadata(truth_dir)
    occ_sensors = occ_sensors[occ_sensors["sensor_type"] == "occupancy_count"]
    if occ_sensors.empty:
        return pd.DataFrame()

    occ_readings = load_all_occupancy_readings(truth_dir)
    if occ_readings.empty:
        return pd.DataFrame()

    timetable = load_timetable(truth_dir)

    rows = []
    for _, sensor in occ_sensors.iterrows():
        sensor_id = sensor["sensor_id"]
        space_id = sensor["space_id"]
        building_id = sensor["building_id"]

        sensor_occ = occ_readings[occ_readings["sensor_id"] == sensor_id].copy()
        if sensor_occ.empty:
            continue
        sensor_occ = sensor_occ.set_index("ts_utc").sort_index()

        # Vectorized approach: merge with timetable for this space
        space_tt = timetable[timetable["space_id"] == space_id].copy()
        if space_tt.empty:
            continue

        # Create interval index for fast interval matching
        for _, event in space_tt.iterrows():
            start = event["start_ts"]
            end = event["end_ts"]
            event_id = event["event_id"]
            module_code = event["module_code"]

            # Find readings in this event window
            mask = (sensor_occ.index >= start) & (sensor_occ.index < end)
            event_readings = sensor_occ.loc[mask]
            if event_readings.empty:
                continue

            # Aggregate to 15-min within event (already at 15-min)
            for ts, value in event_readings["value"].items():
                rows.append({
                    "space_id": space_id,
                    "building_id": building_id,
                    "ts_utc": ts,
                    "observed_occupancy": int(value),
                    "event_id": event["event_id"],
                    "module_code": event["module_code"],
                })

    return pd.DataFrame(rows)