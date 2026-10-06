"""P17 tests for room archetypes."""

from __future__ import annotations

import pandas as pd
import pytest

from src.archetypes import compute_room_archetypes
from pathlib import Path


@pytest.fixture
def truth_dir():
    return Path("data/truth")


def test_archetypes_runs(truth_dir):
    """Archetypes should run and return all rooms with cluster assignments."""
    df = compute_room_archetypes(truth_dir=truth_dir, n_clusters=5)
    assert not df.empty
    assert len(df) == 500  # all spaces
    assert "archetype_id" in df.columns
    assert "archetype_name" in df.columns


def test_archetype_ids_range(truth_dir):
    """Archetype IDs should be in 0..n_clusters-1."""
    df = compute_room_archetypes(truth_dir=truth_dir, n_clusters=5)
    assert df["archetype_id"].between(0, 4).all()
    assert set(df["archetype_id"].unique()) == {0, 1, 2, 3, 4}


def test_archetype_names_meaningful(truth_dir):
    """Archetype names should be non-empty strings."""
    df = compute_room_archetypes(truth_dir=truth_dir, n_clusters=5)
    assert df["archetype_name"].notna().all()
    assert (df["archetype_name"].str.len() > 0).all()


def test_different_n_clusters(truth_dir):
    """Different cluster counts should work."""
    df3 = compute_room_archetypes(truth_dir=truth_dir, n_clusters=3)
    assert df3["archetype_id"].between(0, 2).all()
    assert len(df3) == 500


def test_archetype_distribution(truth_dir):
    """Each archetype should have at least one room."""
    df = compute_room_archetypes(truth_dir=truth_dir, n_clusters=5)
    counts = df["archetype_id"].value_counts()
    assert (counts >= 1).all()


def test_archetype_features_present(truth_dir):
    """Key feature columns should be present."""
    df = compute_room_archetypes(truth_dir=truth_dir, n_clusters=5)
    feature_cols = [
        "avg_co2", "peak_co2", "pct_above_1000", "pct_above_1500",
        "avg_temp", "hours_below_18", "hours_above_24",
        "avg_occ", "max_occ", "pct_zero",
        "total_events", "booked_hours", "util_rate",
        "nia_m2", "capacity",
    ]
    for col in feature_cols:
        assert col in df.columns, f"Missing feature column: {col}"


def test_reproducibility(truth_dir):
    """Same random state should produce identical clusters."""
    df1 = compute_room_archetypes(truth_dir=truth_dir, n_clusters=5, random_state=42)
    df2 = compute_room_archetypes(truth_dir=truth_dir, n_clusters=5, random_state=42)
    assert (df1.sort_values("space_id")["archetype_id"].values == 
            df2.sort_values("space_id")["archetype_id"].values).all()


@pytest.mark.skip(reason="Slow - _build_room_features loads readings per space")
def test_archetype_labeling(truth_dir):
    """Archetype labels should be recognizable strings."""
    df = compute_room_archetypes(truth_dir=truth_dir, n_clusters=3)
    names = set(df["archetype_name"].unique())
    for name in names:
        assert isinstance(name, str)
        assert len(name) > 0