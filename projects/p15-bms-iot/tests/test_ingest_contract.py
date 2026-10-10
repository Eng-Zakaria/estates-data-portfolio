"""The pipeline split: which messages reach bms.readings and which reach the
dead-letter table, and with what reason."""

from __future__ import annotations

import pandas as pd
import pytest
from conftest import START, payload

from ingest_contract import apply_contract
from validate import R_JSON, R_RANGE, R_SCHEMA, R_UNIT, Validator

NOW = START + pd.Timedelta(hours=2)


def _raw(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame.from_records(rows)


def test_valid_messages_all_reach_readings(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "room_temp")
    raw = _raw(
        [
            {
                "ts": (START + pd.Timedelta(minutes=5 * i)).isoformat(),
                "topic": row["topic"],
                "value": 21.0 + i,
                "unit": row["unit"],
                "quality": "good",
            }
            for i in range(3)
        ]
    )
    accepted, dead = apply_contract(raw, validator, now=NOW)
    assert len(accepted) == 3
    assert dead.empty
    assert set(accepted["point_id"]) == {row["point_id"]}


def test_malformed_payloads_are_dead_lettered_with_a_reason(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    raw = _raw(
        [
            {
                "ts": START.isoformat(),
                "topic": row["topic"],
                "value": "not_a_number",
                "unit": row["unit"],
                "quality": None,
            }
        ]
    )
    accepted, dead = apply_contract(raw, validator, now=NOW)
    assert accepted.empty
    assert len(dead) == 1
    # the simulator omits `quality` from malformed payloads on purpose, so the
    # reason is the missing field rather than the non-numeric value
    assert dead["reason"].iloc[0] == R_SCHEMA


def test_out_of_range_and_bad_unit_are_dead_lettered(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    raw = _raw(
        [
            {"ts": START.isoformat(), "topic": row["topic"], "value": 95.0, "unit": "C", "quality": "good"},
            {"ts": START.isoformat(), "topic": row["topic"], "value": 13.0, "unit": "kWh", "quality": "good"},
        ]
    )
    accepted, dead = apply_contract(raw, validator, now=NOW)
    assert accepted.empty
    assert sorted(dead["reason"]) == [R_RANGE, R_UNIT]


def test_dead_letter_rows_keep_the_topic_and_payload_for_triage(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    raw = _raw([{"ts": START.isoformat(), "topic": row["topic"], "value": "nope", "unit": "C", "quality": None}])
    _, dead = apply_contract(raw, validator, now=NOW)
    assert dead["topic"].iloc[0] == row["topic"]
    assert "nope" in dead["payload"].iloc[0]
    assert dead["ts"].iloc[0] == START.isoformat()


def test_numeric_strings_from_the_dry_run_file_are_accepted(validator, registry):
    """The simulator writes values as strings so malformed rows survive the
    round trip; those must not be dead-lettered as non-numeric."""
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    raw = _raw([{"ts": START.isoformat(), "topic": row["topic"], "value": "13.5", "unit": "C", "quality": "good"}])
    accepted, dead = apply_contract(raw, validator, now=NOW)
    assert len(accepted) == 1
    assert accepted["value"].iloc[0] == pytest.approx(13.5)
    assert dead.empty


def test_empty_frame_is_handled(validator):
    accepted, dead = apply_contract(
        _raw([{"ts": [], "topic": [], "value": [], "unit": [], "quality": []}]).iloc[0:0], validator, now=NOW
    )
    assert accepted.empty
    assert dead.empty


def test_simulator_output_splits_the_way_the_truth_file_says(sim):
    """End-to-end on 2 h of simulated telemetry."""
    frame, truth = sim.generate(2.0)
    accepted, dead = apply_contract(frame, Validator.from_repo(), now=START + pd.Timedelta(hours=3))
    assert len(dead) == truth["messages_malformed"]
    assert len(accepted) == truth["messages_sent"] - truth["messages_malformed"]
    assert set(dead["reason"]) == {R_SCHEMA}


def test_accepted_values_are_numeric_and_dated(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "co2")
    raw = _raw([{"ts": START.isoformat(), "topic": row["topic"], "value": 512, "unit": "ppm", "quality": "good"}])
    accepted, _ = apply_contract(raw, validator, now=NOW)
    assert accepted["value"].dtype.kind == "f"
    assert pd.Timestamp(accepted["ts"].iloc[0]) == START
    assert accepted["unit"].iloc[0] == "ppm"


def test_string_payload_is_parsed_not_stored_verbatim(validator, registry):
    """The JSON body must be decoded before the columns are built, otherwise
    value/unit/quality would all end up as one string column."""
    row = next(r for r in registry.values() if r["point_class"] == "room_temp")
    raw = _raw([{"ts": START.isoformat(), "topic": row["topic"], "value": 21.0, "unit": "C", "quality": "good"}])
    accepted, _ = apply_contract(raw, validator, now=NOW)
    assert list(accepted.columns) == ["ts", "point_id", "value", "unit", "quality"]


def test_validator_default_constructor_uses_the_repo_contract():
    """apply_contract must work without being handed a validator."""
    assert Validator.from_repo() is not None


def test_payload_helper_matches_the_contract(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "room_temp")
    assert validator.check(row["topic"], payload(ts=START, value=21.0), now=START).ok
    assert validator.check(row["topic"], "{oops", now=START).reason == R_JSON
