"""Point health and fault detection, on synthetic series with known answers.

Each test builds the smallest frame that contains one known fault, so the
expected finding can be stated by hand rather than inferred from a previous
run of the detector.
"""

from __future__ import annotations

import pandas as pd
import pytest
from conftest import REGISTRY_CSV, START

from health import OUT_OF_HOURS_END, OUT_OF_HOURS_START, DetectionConfig, detect, health_summary

CFG = DetectionConfig(interval_minutes=5)


def frame(rows: list[tuple[str, float]], *, start: pd.Timestamp | None = None, interval: int = 5) -> pd.DataFrame:
    """rows of (point_id, value), one row per (timestamp, point).

    `value` is an object column so a test can drop a non-numeric reading in
    without pandas refusing the assignment.
    """
    base = pd.Timestamp(start or START)
    counts: dict[str, int] = {}
    stamps: list[pd.Timestamp] = []
    for pid, _ in rows:
        n = counts.get(pid, 0)
        counts[pid] = n + 1
        stamps.append(base + pd.Timedelta(minutes=interval * n))
    return pd.DataFrame(
        {
            "ts": stamps,
            "point_id": [pid for pid, _ in rows],
            "value": pd.Series([value for _, value in rows], dtype=object),
            "unit": ["%"] * len(rows),
            "quality": ["good"] * len(rows),
        }
    )


def valve_rows(equip: str, heating: list[float], cooling: list[float]) -> list[tuple[str, float]]:
    """Interleaved valve samples; each valve keeps its own 5-minute cadence."""
    return [
        row
        for h, c in zip(heating, cooling, strict=True)
        for row in ((f"{equip}.heating_valve", h), (f"{equip}.cooling_valve", c))
    ]


# ---------------------------------------------------------------- SEM-01
def test_sem01_fires_when_both_valves_are_open():
    rows = valve_rows("B001.ahu_01", [90.0] * 6, [90.0] * 6)
    findings = detect(frame(rows), REGISTRY_CSV, CFG)
    hits = findings[findings["rule_id"] == "SEM-01"]
    assert len(hits) == 1
    assert hits["point_id"].iloc[0] == "B001.ahu_01.heating_valve"
    assert hits["samples"].iloc[0] == 6


def test_sem01_stays_quiet_when_only_one_valve_is_open():
    rows = valve_rows("B001.ahu_01", [90.0] * 6, [5.0] * 6)
    findings = detect(frame(rows), REGISTRY_CSV, CFG)
    assert (findings["rule_id"] == "SEM-01").sum() == 0


def test_sem01_does_not_fire_below_the_threshold():
    """A modulating valve hovering at 18% is normal, not a fault."""
    rows = valve_rows("B001.ahu_01", [18.0] * 6, [18.0] * 6)
    assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-01").sum() == 0


def test_sem01_separates_equipment_on_the_same_building():
    rows = valve_rows("B001.ahu_01", [90.0] * 6, [5.0] * 6) + valve_rows("B001.ahu_02", [90.0] * 6, [90.0] * 6)
    hits = detect(frame(rows), REGISTRY_CSV, CFG)
    assert hits[hits["rule_id"] == "SEM-01"]["point_id"].tolist() == ["B001.ahu_02.heating_valve"]


# ---------------------------------------------------------------- SEM-02
def test_sem02_fires_on_a_constant_valve_with_a_moving_peer():
    rows = valve_rows("B001.ahu_01", [62.0] * 40, [30.0, 31.0, 32.0, 33.0, 34.0] * 8)
    hits = detect(frame(rows), REGISTRY_CSV, CFG)
    hits = hits[hits["rule_id"] == "SEM-02"]
    assert len(hits) == 1
    assert hits["point_id"].iloc[0] == "B001.ahu_01.heating_valve"
    assert hits["samples"].iloc[0] == 40


def test_sem02_quiet_when_both_valves_are_constant():
    """Two valves that are both at rest is normal overnight plant behaviour."""
    rows = valve_rows("B001.ahu_01", [15.0] * 40, [10.0] * 40)
    assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-02").sum() == 0


def test_sem02_quiet_when_the_constant_run_is_too_short():
    rows = valve_rows("B001.ahu_01", [62.0] * 5, [30.0, 31.0, 32.0, 33.0, 34.0])
    assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-02").sum() == 0


def test_sem02_does_not_fire_across_a_dropout():
    """Samples either side of a comms gap were never delivered, so a frozen
    valve cannot be claimed across the gap."""
    rows = valve_rows("B001.ahu_01", [62.0] * 30, [30.0, 31.0] * 15)
    f = frame(rows)
    # drop 20 timestamps from the middle: a 50-minute hole in each valve series
    f = f.drop(index=[i for i in range(30, 50)])
    assert f["ts"].diff().max() > pd.Timedelta(minutes=20)  # the gap really exists
    hits = detect(f, REGISTRY_CSV, CFG)
    assert (hits["rule_id"] == "SEM-02").sum() == 0


# ---------------------------------------------------------------- SEM-03
def test_sem03_fires_outside_working_hours():
    # 00:00-04:00 local, fan well above the running threshold
    rows = [("B001.ahu_01.fan_speed", 60.0)] * 60
    hits = detect(frame(rows), REGISTRY_CSV, CFG)
    assert (hits["rule_id"] == "SEM-03").sum() == 1


def test_sem03_quiet_during_working_hours():
    noon = pd.Timestamp("2026-10-07T12:00:00+00:00")
    rows = [("B001.ahu_01.fan_speed", 60.0)] * 12
    assert (detect(frame(rows, start=noon), REGISTRY_CSV, CFG)["rule_id"] == "SEM-03").sum() == 0


def test_sem03_quiet_below_the_running_threshold():
    """A trickle of ventilation overnight is not the fault being looked for."""
    rows = [("B001.ahu_01.fan_speed", 18.0)] * 60
    assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-03").sum() == 0


def test_sem03_quiet_at_the_weekend():
    saturday = pd.Timestamp("2026-10-10T10:00:00+00:00")
    assert saturday.day_name() == "Saturday"
    rows = [("B001.ahu_01.fan_speed", 60.0)] * 24
    assert (detect(frame(rows, start=saturday), REGISTRY_CSV, CFG)["rule_id"] == "SEM-03").sum() == 0


def test_working_hours_window_is_the_documented_one():
    assert (OUT_OF_HOURS_START, OUT_OF_HOURS_END) == (7, 19)


# ---------------------------------------------------------------- SEM-04
def test_sem04_fires_on_a_frozen_numeric_point():
    rows = [("B001.room_01.co2", 500.0)] * 80
    hits = detect(frame(rows), REGISTRY_CSV, CFG)
    assert (hits["rule_id"] == "SEM-04").sum() == 1


def test_sem04_reports_the_value_actually_held():
    """The message must name the frozen value, not the first value of the run."""
    rows = [("B001.room_01.co2", 500.0)] * 20 + [("B001.room_01.co2", 900.0)] * 80
    hits = detect(frame(rows), REGISTRY_CSV, CFG)
    flat = hits[hits["rule_id"] == "SEM-04"]
    assert len(flat) == 1
    assert "900.0" in flat["detail"].iloc[0]


def test_sem04_ignores_setpoint_and_occupancy():
    """A setpoint held constant is the system working; an occupancy count is
    legitimately steppy."""
    for point_class in ("setpoint", "occupancy"):
        rows = [(f"B001.room_01.{point_class}", 21.0)] * 80
        assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-04").sum() == 0


# ---------------------------------------------------------------- SEM-05
def test_sem05_fires_on_a_sustained_drift():
    rows = [("B001.room_01.co2", 430.0 + 8.0 * i) for i in range(80)]
    hits = detect(frame(rows), REGISTRY_CSV, CFG)
    hits = hits[hits["rule_id"] == "SEM-05"]
    assert len(hits) == 1
    assert "rising drift" in hits["detail"].iloc[0]


def test_sem05_quiet_on_a_normal_control_ramp():
    """A valve opening towards setpoint is monotone for a couple of hours and
    then settles; the reversal inside the window is what tells them apart."""
    rows = [("B001.ahu_01.cooling_valve", float(v)) for v in (10, 20, 35, 50, 55, 50, 40, 25, 15, 11, 10, 10) * 8]
    assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-05").sum() == 0


def test_sem05_quiet_on_a_short_ramp():
    """A fast but short move is control action, not drift."""
    rows = [("B001.ahu_01.cooling_valve", 10.0 + 5.0 * i) for i in range(10)] * 6
    assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-05").sum() == 0


def test_sem05_quiet_on_small_measurement_noise():
    rows = [("B001.room_01.room_temp", 21.0 + (0.5 if i % 2 else -0.5)) for i in range(80)]
    assert (detect(frame(rows), REGISTRY_CSV, CFG)["rule_id"] == "SEM-05").sum() == 0


def test_sem05_works_for_falling_drift():
    rows = [("B001.room_01.co2", 2000.0 - 12.0 * i) for i in range(80)]
    hits = detect(frame(rows), REGISTRY_CSV, CFG)
    assert "falling drift" in hits[hits["rule_id"] == "SEM-05"]["detail"].iloc[0]


# ---------------------------------------------------------------- staleness
def test_staleness_fires_on_a_gap():
    base = pd.Timestamp(START)
    f = pd.DataFrame(
        {
            "ts": [
                base,
                base + pd.Timedelta(minutes=5),
                base + pd.Timedelta(minutes=10),
                base + pd.Timedelta(minutes=125),
                base + pd.Timedelta(minutes=130),
            ],
            "point_id": ["B001.room_01.room_temp"] * 5,
            "value": [21.0] * 5,
            "unit": ["C"] * 5,
            "quality": ["good"] * 5,
        }
    )
    hits = detect(f, REGISTRY_CSV, CFG)
    stale = hits[hits["rule_id"] == "STALENESS"]
    assert len(stale) == 1
    assert "115 min" in stale["detail"].iloc[0]


def test_staleness_quiet_on_a_single_missed_sample():
    base = pd.Timestamp(START)
    f = pd.DataFrame(
        {
            "ts": [base, base + pd.Timedelta(minutes=15), base + pd.Timedelta(minutes=20)],
            "point_id": ["B001.room_01.room_temp"] * 3,
            "value": [21.0, 21.1, 21.0],
            "unit": ["C"] * 3,
            "quality": ["good"] * 3,
        }
    )
    assert (detect(f, REGISTRY_CSV, CFG)["rule_id"] == "STALENESS").sum() == 0


# ---------------------------------------------------------------- structure
def test_empty_input_returns_an_empty_frame_with_the_documented_columns():
    out = detect(pd.DataFrame(columns=["ts", "point_id", "value", "unit", "quality"]), REGISTRY_CSV, CFG)
    assert out.empty
    assert list(out.columns) == ["rule_id", "point_id", "start_ts", "end_ts", "samples", "detail"]


def test_non_numeric_values_are_dropped_rather_than_crashing():
    f = frame([("B001.room_01.co2", 500.0)] * 40)
    f.loc[3, "value"] = "not_a_number"
    assert isinstance(detect(f, REGISTRY_CSV, CFG), pd.DataFrame)


def test_findings_are_sorted_deterministically():
    rows = valve_rows("B001.ahu_01", [90.0] * 8, [90.0] * 8) + [("B001.room_01.co2", 500.0)] * 80
    first = detect(frame(rows), REGISTRY_CSV, CFG)
    second = detect(frame(rows), REGISTRY_CSV, CFG)
    assert first.equals(second)
    assert list(first.columns) == list(second.columns)


def test_stuck_valve_is_not_reported_twice():
    """A stuck valve is also a flat-line; the alert queue gets one row."""
    rows = valve_rows("B001.ahu_01", [62.0] * 80, [30.0, 31.0, 32.0, 33.0, 34.0] * 16)
    findings = detect(frame(rows), REGISTRY_CSV, CFG)
    stuck = findings[findings["rule_id"] == "SEM-02"]
    assert len(stuck) == 1
    covered = findings[
        (findings["rule_id"] == "SEM-04")
        & (findings["point_id"] == stuck["point_id"].iloc[0])
        & (findings["start_ts"] >= stuck["start_ts"].iloc[0])
        & (findings["end_ts"] <= stuck["end_ts"].iloc[0])
    ]
    assert covered.empty


# ---------------------------------------------------------------- health
def test_health_summary_reports_every_registry_point():
    summary = health_summary(frame([("B001.room_01.co2", 500.0)] * 10), REGISTRY_CSV, CFG)
    assert len(summary) == 294
    assert set(summary["point_id"]) == set(pd.read_csv(REGISTRY_CSV)["point_id"])


def test_health_summary_flags_a_point_with_no_data():
    summary = health_summary(frame([("B001.room_01.co2", 500.0)] * 10), REGISTRY_CSV, CFG)
    missing = summary[summary["point_id"] == "B001.ahu_01.supply_temp"]
    assert missing["samples"].iloc[0] == 0
    assert not bool(missing["healthy"].iloc[0])


def test_health_summary_completeness_is_a_percentage():
    summary = health_summary(frame([("B001.room_01.co2", 500.0)] * 12), REGISTRY_CSV, CFG)
    row = summary[summary["point_id"] == "B001.room_01.co2"]
    assert row["completeness_pct"].iloc[0] == pytest.approx(100.0)
    assert row["last_seen"].iloc[0] == pd.Timestamp(START) + pd.Timedelta(minutes=55)


def test_health_summary_counts_suspect_quality():
    f = frame([("B001.room_01.co2", 500.0)] * 10)
    f.loc[0, "quality"] = "suspect"
    summary = health_summary(f, REGISTRY_CSV, CFG)
    row = summary[summary["point_id"] == "B001.room_01.co2"]
    assert row["pct_suspect_quality"].iloc[0] == pytest.approx(10.0)


def test_health_summary_marks_a_gappy_point_unhealthy():
    base = pd.Timestamp(START)
    f = pd.DataFrame(
        {
            "ts": [base, base + pd.Timedelta(minutes=240)],
            "point_id": ["B001.room_01.co2"] * 2,
            "value": [500.0, 501.0],
            "unit": ["ppm"] * 2,
            "quality": ["good"] * 2,
        }
    )
    summary = health_summary(f, REGISTRY_CSV, CFG)
    row = summary[summary["point_id"] == "B001.room_01.co2"]
    assert row["max_gap_minutes"].iloc[0] == 240.0
    assert not bool(row["healthy"].iloc[0])
