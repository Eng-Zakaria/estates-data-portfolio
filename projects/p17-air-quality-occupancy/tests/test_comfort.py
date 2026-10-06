"""P17 tests for thermal comfort analysis."""

from __future__ import annotations

import pandas as pd
import pytest

from src.comfort import compute_thermal_comfort, compute_comfort_risk_score
from pathlib import Path


@pytest.fixture
def truth_dir():
    return Path("data/truth")


def test_thermal_comfort_runs(truth_dir):
    """Thermal comfort metrics should run without error and return expected columns."""
    df = compute_thermal_comfort(truth_dir=truth_dir)
    assert not df.empty
    expected_cols = [
        "space_id", "building_id", "space_category", "nia_m2", "capacity_seats",
        "sensor_id", "occupied_hours", "total_hours", "occupancy_pct",
        "avg_temp_c", "min_temp_c", "max_temp_c",
        "hours_below_comfort", "hours_above_comfort", "overheating_hours",
        "pct_time_below_comfort", "pct_time_above_comfort", "pct_overheating_time"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"


def test_thermal_comfort_risk_score(truth_dir):
    """Risk score should be in 0-100 range."""
    df = compute_thermal_comfort(truth_dir=truth_dir)
    df = compute_comfort_risk_score(df)
    assert df["comfort_risk_score"].between(0, 100).all()


def test_no_negative_hours(truth_dir):
    """Hours metrics should be non-negative."""
    df = compute_thermal_comfort(truth_dir=truth_dir)
    assert (df["hours_below_comfort"] >= 0).all()
    assert (df["hours_above_comfort"] >= 0).all()
    assert (df["overheating_hours"] >= 0).all()


def test_pct_ranges(truth_dir):
    """Percentage metrics should be in 0-100 range."""
    df = compute_thermal_comfort(truth_dir=truth_dir)
    assert df["pct_time_below_comfort"].between(0, 100).all()
    assert df["pct_time_above_comfort"].between(0, 100).all()
    assert df["pct_overheating_time"].between(0, 100).all()


def test_temp_reasonable(truth_dir):
    """Temperature values should be physically reasonable."""
    df = compute_thermal_comfort(truth_dir=truth_dir)
    assert (df["avg_temp_c"] > -20).all()
    assert (df["avg_temp_c"] < 50).all()
    assert (df["min_temp_c"] <= df["avg_temp_c"]).all()
    assert (df["max_temp_c"] >= df["avg_temp_c"]).all()


def test_comfort_risk_score_ordering(truth_dir):
    """Rooms with more overheating hours should have higher risk scores."""
    df = compute_thermal_comfort(truth_dir=truth_dir)
    df = compute_comfort_risk_score(df)
    df_sorted = df.sort_values("overheating_hours")
    top_overheat = df_sorted.tail(3)["space_id"].tolist()
    top_risk = df.sort_values("comfort_risk_score").tail(3)["space_id"].tolist()
    assert len(set(top_overheat) & set(top_risk)) >= 1


def test_custom_thresholds(truth_dir):
    """Custom comfort thresholds should be respected."""
    df = compute_thermal_comfort(truth_dir=truth_dir, comfort_min_c=20, comfort_max_c=22, overheating_c=25)
    assert not df.empty