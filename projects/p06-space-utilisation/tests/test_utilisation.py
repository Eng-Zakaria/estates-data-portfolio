"""Hand-checked fixtures for P06 utilisation KPIs."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utilisation import (  # noqa: E402
    frequency_rate,
    is_capacity_mismatch,
    is_no_show,
    m2_per_fte,
    occupancy_rate,
    releasable_rooms,
    utilisation,
    variance_to_median,
)


def test_acceptance_one_room_three_events() -> None:
    # One room, capacity 40, available 45h (5 days x 9h).
    # 3 events x 2h = 6 booked hours; groups 20, 30, 10 (avg 20).
    booked, available = 6.0, 45.0
    freq = frequency_rate(booked, available)
    assert freq == pytest.approx(6.0 / 45.0)  # 0.1333
    occ = occupancy_rate(20.0, 40)
    assert occ == pytest.approx(0.5)
    assert utilisation(freq, occ) == pytest.approx(0.1333 * 0.5, rel=1e-3)
    # Capacity mismatch: only the group-10 event (< 50% of 40).
    assert is_capacity_mismatch(20, 40) is False
    assert is_capacity_mismatch(10, 40) is True


def test_frequency() -> None:
    assert frequency_rate(9.0, 45.0) == pytest.approx(0.2)
    assert frequency_rate(9.0, 0.0) is None
    assert frequency_rate(0.0, 45.0) == pytest.approx(0.0)


def test_occupancy() -> None:
    assert occupancy_rate(30.0, 40) == pytest.approx(0.75)
    assert occupancy_rate(30.0, 0) is None
    assert occupancy_rate(30.0, None) is None


def test_utilisation() -> None:
    assert utilisation(0.7, 0.3) == pytest.approx(0.21)
    assert utilisation(None, 0.3) is None


def test_no_show() -> None:
    assert is_no_show(8, 0.0) is True
    assert is_no_show(8, 12.0) is False
    assert is_no_show(0, None) is None  # no coverage: unknown
    assert is_no_show(8, None) is True  # readings exist, all invalid/zero


def test_m2_per_fte_and_variance() -> None:
    assert m2_per_fte(14851.9, 60.0) == pytest.approx(247.5317, rel=1e-4)
    assert m2_per_fte(100.0, 0.0) is None
    assert variance_to_median(247.5, 64.3) == pytest.approx(2.849, rel=1e-3)
    assert variance_to_median(100.0, 0.0) is None


def test_releasable() -> None:
    # 30 rooms at 12% utilisation with a 40% target -> 21 releasable.
    assert releasable_rooms(30, 0.12, 0.40) == pytest.approx(21.0)
    assert releasable_rooms(30, None, 0.40) is None
    assert releasable_rooms(30, 0.12, 0.0) is None
