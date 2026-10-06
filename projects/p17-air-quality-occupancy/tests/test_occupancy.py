"""P17 tests for occupancy analysis."""

from __future__ import annotations

import pandas as pd
import pytest

from src.occupancy import compute_occupancy_analysis, compute_occupancy_utilization_score
from pathlib import Path


@pytest.fixture
def truth_dir():
    return Path("data/truth")


def test_occupancy_analysis_runs(truth_dir):
    """Occupancy analysis should run without error and return expected columns."""
    df = compute_occupancy_analysis(truth_dir=truth_dir)
    assert not df.empty
    expected_cols = [
        "space_id", "building_id", "space_category", "nia_m2", "capacity_seats",
        "sensor_id", "total_events", "no_show_count", "no_show_rate_pct",
        "overcapacity_count", "overcapacity_rate_pct", "avg_actual_occupancy",
        "max_actual_occupancy", "avg_group_size", "utilization_rate_pct"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"


def test_occupancy_risk_score(truth_dir):
    """Utilization risk score should be in 0-100 range."""
    df = compute_occupancy_analysis(truth_dir=truth_dir)
    df = compute_occupancy_utilization_score(df)
    assert df["utilization_risk_score"].between(0, 100).all()


def test_no_show_rate_bounds(truth_dir):
    """No-show rate should be 0-100%."""
    df = compute_occupancy_analysis(truth_dir=truth_dir)
    assert df["no_show_rate_pct"].between(0, 100).all()


def test_overcapacity_rate_bounds(truth_dir):
    """Overcapacity rate should be 0-100%."""
    df = compute_occupancy_analysis(truth_dir=truth_dir)
    assert df["overcapacity_rate_pct"].between(0, 100).all()


def test_utilization_rate_bounds(truth_dir):
    """Utilization rate should be non-negative."""
    df = compute_occupancy_analysis(truth_dir=truth_dir)
    assert (df["utilization_rate_pct"] >= 0).all()


def test_actual_vs_group_size(truth_dir):
    """Actual occupancy should be related to group size."""
    df = compute_occupancy_analysis(truth_dir=truth_dir)
    assert (df["avg_actual_occupancy"] <= df["max_actual_occupancy"]).all()


def test_no_show_reasonable(truth_dir):
    """No-show count should not exceed total events."""
    df = compute_occupancy_analysis(truth_dir=truth_dir)
    assert (df["no_show_count"] <= df["total_events"]).all()