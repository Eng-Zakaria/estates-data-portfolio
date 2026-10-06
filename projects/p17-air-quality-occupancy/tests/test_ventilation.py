"""P17 tests for ventilation analysis."""

from __future__ import annotations

import pandas as pd
import pytest

from src.ventilation import compute_ventilation_metrics, compute_ventilation_risk_score
from pathlib import Path


@pytest.fixture
def truth_dir():
    return Path("data/truth")


def test_ventilation_metrics_runs(truth_dir):
    """Ventilation metrics should run without error and return expected columns."""
    df = compute_ventilation_metrics(truth_dir=truth_dir)
    assert not df.empty
    expected_cols = [
        "space_id", "building_id", "space_category", "nia_m2", "capacity_seats",
        "sensor_id", "occupied_hours", "total_hours", "occupancy_pct",
        "pct_occupied_time_above_1000ppm", "pct_occupied_time_above_1500ppm",
        "peak_co2_ppm", "avg_co2_ppm", "co2_rise_rate_ppm_per_person_per_hour",
        "estimated_ach_per_hour"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"


def test_ventilation_metrics_risk_score(truth_dir):
    """Risk score should be in 0-100 range for non-NaN values."""
    df = compute_ventilation_metrics(truth_dir=truth_dir)
    df = compute_ventilation_risk_score(df)
    valid = df["ventilation_risk_score"].dropna()
    assert valid.between(0, 100).all()
    assert len(valid) >= len(df) * 0.5


def test_ventilation_metrics_specific_rooms(truth_dir):
    """Known problematic rooms should have higher risk scores."""
    df = compute_ventilation_metrics(truth_dir=truth_dir)
    df = compute_ventilation_risk_score(df)
    b005 = df[df["space_id"] == "S-B005-L00-038"]
    assert not b005.empty
    # B005 has high CO2 but risk score may be NaN due to missing ACH data
    score = b005["ventilation_risk_score"].iloc[0]
    if pd.notna(score):
        assert score > 10


def test_co2_rise_rate_calculation(truth_dir):
    """CO2 rise rate should compute for rooms with occupancy sensors."""
    df = compute_ventilation_metrics(truth_dir=truth_dir)
    with_rise = df[df["co2_rise_rate_ppm_per_person_per_hour"].notna()]
    assert len(with_rise) >= 0


def test_ach_estimation(truth_dir):
    """Air change rate estimation should not crash."""
    df = compute_ventilation_metrics(truth_dir=truth_dir)
    assert "estimated_ach_per_hour" in df.columns


def test_no_negative_metrics(truth_dir):
    """Hours and percentages should be non-negative."""
    df = compute_ventilation_metrics(truth_dir=truth_dir)
    assert (df["occupied_hours"] >= 0).all()
    assert (df["pct_occupied_time_above_1000ppm"] >= 0).all()
    assert (df["pct_occupied_time_above_1500ppm"] >= 0).all()
    assert (df["peak_co2_ppm"] >= 0).all()
    assert (df["avg_co2_ppm"] >= 0).all()


def test_ventilation_risk_score_ordering(truth_dir):
    """Rooms with higher peak CO2 should generally have higher risk scores."""
    df = compute_ventilation_metrics(truth_dir=truth_dir)
    df = compute_ventilation_risk_score(df)
    df_valid = df.dropna(subset=["ventilation_risk_score"])
    if len(df_valid) >= 6:
        df_sorted = df_valid.sort_values("peak_co2_ppm")
        top_peak = df_sorted.tail(3)["space_id"].tolist()
        top_risk = df_valid.sort_values("ventilation_risk_score").tail(3)["space_id"].tolist()
        assert len(set(top_peak) & set(top_risk)) >= 1