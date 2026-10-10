"""Simulator: payload shape, plausibility, determinism and fault injection."""

from __future__ import annotations

import json
from datetime import UTC, timedelta

import pandas as pd
import pytest
from conftest import START

from simulator import FAULT_WINDOWS, FAULTS, Simulator, occupancy_people


def test_registry_backed_point_count(sim):
    assert len(sim.points) == 294
    assert len({p["point_id"] for p in sim.points}) == 294
    assert {p["building"] for p in sim.points} == {"B001", "B003", "B007"}


def test_generated_values_are_within_the_contract_ranges(sim, rules):
    """A simulator that emits out-of-range values would be dead-lettered for
    reasons that have nothing to do with the faults under test."""
    frame, _ = sim.generate(1.0)
    numeric = frame[~frame["malformed"]].copy()
    numeric["value"] = numeric["value"].astype(float)
    registry = {p["point_id"]: p for p in sim.points}
    for point_id, grp in numeric.groupby("point_id"):
        rule = rules["rules_by_point_class"][registry[point_id]["point_class"]]
        assert grp["value"].between(rule["min"], rule["max"]).all(), point_id


def test_payload_shape_is_the_contract_payload(sim, validator):
    frame, _ = sim.generate(0.5)
    for row in frame[~frame["malformed"]].itertuples():
        body = json.dumps({"ts": row.ts, "value": float(row.value), "unit": row.unit, "quality": row.quality})
        result = validator.check(row.topic, body, now=START + timedelta(hours=2))
        assert result.ok, (row.topic, result.reason)


def test_well_formed_rows_pass_the_validator_and_malformed_ones_do_not(sim, validator):
    """Every non-malformed row must be accepted, so ingestion losses are only
    ever attributable to an injected fault."""
    frame, truth = sim.generate(1.0)
    valid, rejected = 0, 0
    for row in frame.itertuples():
        try:
            value = float(row.value)
        except (TypeError, ValueError):
            rejected += 1
            continue
        body = json.dumps({"ts": row.ts, "value": value, "unit": row.unit, "quality": row.quality})
        if validator.check(row.topic, body, now=START + timedelta(hours=2)).ok:
            valid += 1
        else:
            rejected += 1
    # every well-formed message must be accepted; anything else would make an
    # ingestion loss look like a detection failure
    assert valid == truth["messages_sent"] - truth["messages_malformed"]
    assert rejected == truth["messages_malformed"]


def test_message_count_matches_points_times_steps(sim):
    frame, truth = sim.generate(2.0)  # 24 steps at a 5-min cadence
    assert truth["messages_sent"] == 294 * 24 - truth["messages_dropped_comms_dropout"]
    assert len(frame) == truth["messages_sent"]


def test_malformed_rows_omit_the_quality_field(sim):
    """The pipeline's MISSING_FIELD reason is exercised end to end only if the
    simulator really does send payloads missing a required field."""
    frame, truth = sim.generate(1.0)
    malformed = frame[frame["malformed"]]
    assert len(malformed) == truth["messages_malformed"] > 0
    assert malformed["quality"].isna().all()
    assert malformed["value"].astype(str).str.startswith("not_a_number").all()


def test_same_seed_gives_identical_output():
    a = Simulator(START, seed=42).generate(1.0)[0]
    b = Simulator(START, seed=42).generate(1.0)[0]
    assert a.equals(b)


def test_different_seeds_differ():
    a = Simulator(START, seed=1).generate(1.0)[0]
    b = Simulator(START, seed=2).generate(1.0)[0]
    assert not a.equals(b)


def test_fault_plan_is_deterministic_and_covers_every_type():
    sim = Simulator(START, seed=42)
    types = {f.fault for f in sim.plan}
    assert types == set(FAULTS)
    assert len(sim.plan) == 20  # 4 windows per type
    again = Simulator(START, seed=42)
    assert [f.point_id for f in sim.plan] == [f.point_id for f in again.plan]


def test_simultaneous_heat_cool_avoids_the_stuck_valve_equipment():
    """Otherwise one injected fault is credited with the other's detection."""
    sim = Simulator(START, seed=42)
    stuck = {f.point_id for f in sim.plan if f.fault == "stuck_valve"}
    both = {f.point_id for f in sim.plan if f.fault == "simultaneous_heat_cool"}
    assert not (stuck & both)


def test_fault_windows_do_not_overlap_on_the_same_point_class():
    """Windows that share a point class can mask each other's detection."""
    by_class = {
        "stuck_valve": "heating_valve",
        "simultaneous_heat_cool": "heating_valve",
        "sensor_drift": "co2",
        "comms_dropout": "room_temp",
        "out_of_hours": "fan_speed",
    }
    windows = FAULT_WINDOWS
    overlapping = [
        (a, b)
        for a in FAULTS
        for b in FAULTS
        if a < b and by_class[a] == by_class[b] and windows[a][0] < windows[b][1] and windows[b][0] < windows[a][1]
    ]
    assert overlapping == []


def _row(sim, fault: str):
    truth = next(f for f in sim.plan if f.fault == fault)
    return next(r for r in sim.points if r["point_id"] == truth.point_id), truth


def _window(frame, point_id: str, truth) -> pd.DataFrame:
    return frame[
        (frame["point_id"] == point_id)
        & (frame["ts"] >= (START + timedelta(minutes=truth.start_minute)).isoformat())
        & (frame["ts"] < (START + timedelta(minutes=truth.end_minute)).isoformat())
    ]


def test_comms_dropout_publishes_nothing_for_the_window(sim):
    row, truth = _row(sim, "comms_dropout")
    frame, _ = sim.generate(24.0)
    during = _window(frame, row["point_id"], truth)
    assert during.empty


def test_stuck_valve_is_constant_across_its_window(sim):
    row, truth = _row(sim, "stuck_valve")
    frame, _ = sim.generate(24.0)
    during = _window(frame, row["point_id"], truth)
    assert not during.empty
    assert during["value"].nunique() == 1


def test_stuck_valve_peer_keeps_moving(sim):
    """SEM-02 needs a moving peer valve; if it stopped too the fault is invisible."""
    _, truth = _row(sim, "stuck_valve")
    frame, _ = sim.generate(24.0)
    peer = _window(frame, truth.peer_point_id, truth)["value"].astype(float)
    assert not peer.empty
    assert peer.max() - peer.min() > 1.0


def test_drift_stays_inside_the_contract_ceiling(sim):
    """A drifting sensor that trips the range check would be scored as a data
    quality failure rather than as a drift finding."""
    _, truth = _row(sim, "sensor_drift")
    frame, _ = sim.generate(24.0)
    values = _window(frame, truth.point_id, truth)["value"].astype(float)
    assert values.is_monotonic_increasing
    assert values.max() <= 10000


def test_faulty_rows_are_marked_suspect_quality(sim):
    _, truth = _row(sim, "stuck_valve")
    frame, _ = sim.generate(24.0)
    during = _window(frame, truth.point_id, truth)
    assert (during["quality"] == "suspect").all()


def test_occupancy_is_empty_overnight_and_at_weekends():
    from datetime import datetime

    wednesday_03 = datetime(2026, 10, 7, 3, tzinfo=UTC)
    saturday_noon = datetime(2026, 10, 10, 12, tzinfo=UTC)
    assert occupancy_people(wednesday_03, 40) == 0
    assert occupancy_people(saturday_noon, 40) == 0


def test_occupancy_peaks_in_the_working_day():
    from datetime import datetime

    peak = max(occupancy_people(datetime(2026, 10, 7, h, tzinfo=UTC), 40) for h in range(24))
    assert peak > 20


def test_truth_file_records_everything_needed_to_score_detection(sim):
    _, truth = sim.generate(0.5)
    assert truth["seed"] == 7
    assert truth["interval_minutes"] == 5
    assert truth["points"] == 294
    for fault in truth["faults"]:
        assert set(fault) == {
            "fault",
            "point_id",
            "peer_point_id",
            "start_minute",
            "end_minute",
            "detection_rule",
            "detail",
        }
        assert fault["detection_rule"] in {"SEM-01", "SEM-02", "SEM-03", "SEM-04", "SEM-05", "STALENESS"}
        assert fault["end_minute"] > fault["start_minute"]


def test_no_faults_means_a_clean_run():
    sim = Simulator(START, seed=42, faults=[])
    assert sim.plan == []
    _, truth = sim.generate(0.5)
    assert truth["faults"] == []


@pytest.mark.parametrize("fault", FAULTS)
def test_each_fault_can_be_requested_on_its_own(fault):
    sim = Simulator(START, seed=42, faults=[fault])
    assert {f.fault for f in sim.plan} == {fault}
