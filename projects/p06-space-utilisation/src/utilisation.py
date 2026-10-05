"""Space utilisation KPIs (P06) — pure functions, SMG-style frequency x occupancy.

All data synthetic. Window/availability definitions live with callers;
see methodology.md.
"""

from __future__ import annotations


def frequency_rate(booked_hours: float, available_hours: float) -> float | None:
    """Timetabled hours / available hours. None when no availability."""
    if available_hours is None or available_hours <= 0:
        return None
    return booked_hours / available_hours


def occupancy_rate(avg_group_size: float, capacity_seats: int | None) -> float | None:
    """Average attendance / room capacity while in use. None when no capacity."""
    if capacity_seats is None or capacity_seats <= 0:
        return None
    return avg_group_size / capacity_seats


def utilisation(freq: float | None, occ: float | None) -> float | None:
    """Utilisation = frequency x occupancy (SMG-style)."""
    if freq is None or occ is None:
        return None
    return freq * occ


def is_no_show(n_readings: int, max_observed: float | None) -> bool | None:
    """Booked event with sensor coverage but ~zero observed occupancy.

    None when there is no sensor coverage (unknown, not a no-show).
    Negative/invalid readings are excluded upstream.
    """
    if n_readings == 0:
        return None
    return (max_observed if max_observed is not None else 0.0) < 1.0


def is_capacity_mismatch(group_size: int, capacity_seats: int | None) -> bool | None:
    """Group smaller than half the room capacity. None when no capacity."""
    if capacity_seats is None or capacity_seats <= 0:
        return None
    return group_size < 0.5 * capacity_seats


def m2_per_fte(nia_m2: float, fte: float | None) -> float | None:
    """Floor area per FTE. None when FTE missing/non-positive."""
    if fte is None or fte <= 0:
        return None
    return nia_m2 / fte


def variance_to_median(value: float, median: float | None) -> float | None:
    """(value - median) / median. None when median missing/zero."""
    if median is None or median == 0:
        return None
    return (value - median) / median


def releasable_rooms(n_rooms: int, avg_utilisation: float | None, target: float) -> float | None:
    """Rooms releasable if utilisation rose to target: n * (1 - util/target)."""
    if avg_utilisation is None or target is None or target <= 0:
        return None
    return n_rooms * (1.0 - avg_utilisation / target)
