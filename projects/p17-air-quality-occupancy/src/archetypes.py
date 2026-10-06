"""P17 Room archetypes (k-means clustering on usage/CO2 profiles)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .config import get_settings
from .data import (
    load_all_sensor_metadata,
    load_all_co2_readings,
    load_all_temp_readings,
    load_all_occupancy_readings,
    load_spaces,
    load_timetable,
    load_readings,
)


def _build_room_features(
    truth_dir: Path | None = None,
) -> pd.DataFrame:
    """Build feature matrix per room from sensor data and timetable."""
    settings = get_settings()
    truth_dir = truth_dir or settings.truth_dir

    sensors = load_all_sensor_metadata(truth_dir)
    spaces = load_spaces(truth_dir)
    timetable = load_timetable(truth_dir)

    # CO2 metrics
    co2_sensors = sensors[sensors["sensor_type"] == "co2"]
    co2_readings = load_all_co2_readings(truth_dir)

    # Temp metrics
    temp_sensors = sensors[sensors["sensor_type"] == "temp"]
    temp_readings = load_all_temp_readings(truth_dir)

    # Occupancy metrics
    occ_sensors = sensors[sensors["sensor_type"] == "occupancy_count"]
    occ_readings = load_all_occupancy_readings(truth_dir)

    # Timetable stats
    tt_stats = timetable.groupby("space_id").agg(
        total_events=("event_id", "count"),
        avg_duration_hours=("event_id", lambda x: 2.0),  # placeholder
        total_booked_hours=("event_id", lambda x: len(x) * 2.0),
    ).reset_index()

    room_features = []
    for _, space in spaces.iterrows():
        space_id = space["space_id"]
        building_id = space["building_id"]
        space_category = space["space_category"]
        nia_m2 = float(space["nia_m2"])
        capacity = int(space["capacity_seats"])

        # CO2 features
        space_co2_sensors = co2_sensors[co2_sensors["space_id"] == space_id]
        co2_metrics = {"avg_co2": 0, "peak_co2": 0, "pct_above_1000": 0, "pct_above_1500": 0}
        if not space_co2_sensors.empty:
            sensor_id = space_co2_sensors.iloc[0]["sensor_id"]
            sensor_data = load_readings(sensor_ids=[sensor_id], truth_dir=truth_dir)
            if not sensor_data.empty:
                vals = sensor_data["value"]
                co2_metrics = {
                    "avg_co2": float(vals.mean()),
                    "peak_co2": float(vals.max()),
                    "pct_above_1000": float((vals > 1000).mean() * 100),
                    "pct_above_1500": float((vals > 1500).mean() * 100),
                }

        # Temperature features
        space_temp_sensors = temp_sensors[temp_sensors["space_id"] == space_id]
        temp_metrics = {"avg_temp": 0, "hours_below_18": 0, "hours_above_24": 0}
        if not space_temp_sensors.empty:
            sensor_id = space_temp_sensors.iloc[0]["sensor_id"]
            sensor_data = load_readings(sensor_ids=[sensor_id], truth_dir=truth_dir)
            if not sensor_data.empty:
                vals = sensor_data["value"]
                temp_metrics = {
                    "avg_temp": float(vals.mean()),
                    "hours_below_18": float((vals < 18).sum() * 0.25),
                    "hours_above_24": float((vals > 24).sum() * 0.25),
                }

        # Occupancy features
        space_occ_sensors = occ_sensors[occ_sensors["space_id"] == space_id]
        occ_metrics = {"avg_occ": 0, "max_occ": 0, "pct_zero": 100}
        if not space_occ_sensors.empty:
            sensor_id = space_occ_sensors.iloc[0]["sensor_id"]
            sensor_data = load_readings(sensor_ids=[sensor_id], truth_dir=truth_dir)
            if not sensor_data.empty:
                vals = sensor_data["value"]
                occ_metrics = {
                    "avg_occ": float(vals.mean()),
                    "max_occ": float(vals.max()),
                    "pct_zero": float((vals == 0).mean() * 100),
                }

        # Timetable utilization
        util = {"total_events": 0, "booked_hours": 0, "util_rate": 0}
        if space_id in tt_stats["space_id"].values:
            row = tt_stats[tt_stats["space_id"] == space_id].iloc[0]
            util = {
                "total_events": int(row["total_events"]),
                "booked_hours": float(row["total_booked_hours"]),
                "util_rate": min(100, float(row["total_booked_hours"]) / 2000 * 100),  # rough
            }

        room_features.append({
            "space_id": space_id,
            "building_id": building_id,
            "space_category": space["space_category"],
            "nia_m2": nia_m2,
            "capacity": int(space["capacity_seats"]),
            **co2_metrics,
            **temp_metrics,
            **occ_metrics,
            **util,
        })

    return pd.DataFrame(room_features)


def compute_room_archetypes(
    truth_dir: Path | None = None,
    n_clusters: int | None = None,
    random_state: int | None = None,
) -> pd.DataFrame:
    """Cluster rooms into archetypes based on usage and environmental profiles."""
    settings = get_settings()
    truth_dir = truth_dir or settings.truth_dir
    n_clusters = n_clusters or settings.archetype_n_clusters
    random_state = random_state or settings.archetype_random_state

    features_df = _build_room_features(truth_dir)
    if features_df.empty or len(features_df) < n_clusters:
        return pd.DataFrame()

    # Feature columns for clustering
    feature_cols = [
        "avg_co2", "peak_co2", "pct_above_1000", "pct_above_1500",
        "avg_temp", "hours_below_18", "hours_above_24",
        "avg_occ", "max_occ", "pct_zero",
        "total_events", "booked_hours", "util_rate",
        "nia_m2", "capacity",
    ]
    # Ensure all columns exist
    feature_cols = [c for c in feature_cols if c in features_df.columns]
    X = features_df[feature_cols].fillna(0)

    # Scale
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # K-means
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Add cluster labels
    features_df = features_df.copy()
    features_df["archetype_id"] = labels
    features_df["archetype_name"] = features_df["archetype_id"].map(_label_archetypes(kmeans, feature_cols))

    return features_df


def _label_archetypes(kmeans: KMeans, feature_cols: list[str]) -> dict[int, str]:
    """Generate plain-English labels for archetype clusters based on centroids."""
    centers = kmeans.cluster_centers_
    labels = {}
    for i, center in enumerate(centers):
        # Map feature indices
        feat_dict = dict(zip(feature_cols, center))

        # Heuristic labeling
        if feat_dict.get("avg_co2", 0) > 800:
            name = "High CO₂ Lecture"
        elif feat_dict.get("avg_occ", 0) > 20:
            name = "Busy Collaborative"
        elif feat_dict.get("util_rate", 0) < 20:
            name = "Underused"
        elif feat_dict.get("avg_co2", 0) < 500 and feat_dict.get("pct_zero", 0) > 80:
            name = "Storage / Low Use"
        elif feat_dict.get("hours_below_18", 0) > 100:
            name = "Cold / Underheated"
        elif feat_dict.get("hours_above_24", 0) > 100:
            name = "Overheated"
        else:
            name = f"Standard {i+1}"
        labels[i] = name
    return labels