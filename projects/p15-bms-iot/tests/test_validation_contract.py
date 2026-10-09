"""The ingestion contract: what the pipeline accepts and what it dead-letters.

Two things are checked here. First, the rules the Python reference enforces
(`src/validate.py`) against the rules the running Node-RED flow enforces
(`contracts/validation_rules.json` and the flow's JS). If those drift apart the
tests pass while production behaves differently, which is the failure mode that
matters most here. Second, that each rejection reason is reachable and means
what the README says it means.
"""

from __future__ import annotations

import json
import re
from datetime import timedelta

import pytest
from conftest import FLOW_MERGED, START, payload

from validate import R_JSON, R_QUALITY, R_RANGE, R_SCHEMA, R_TOPIC, R_TS_FORMAT, R_TS_FUTURE, R_TS_OLD
from validate import R_UNIT, R_UNKNOWN_POINT, R_VALUE, normalise_unit, to_celsius


def _check(validator, topic, body, **kwargs):
    return validator.check(topic, body, **kwargs)


# --------------------------------------------------------------------- sync
def test_reason_codes_exist_on_both_sides(registry, rules):
    """Every reason the Python validator can emit is a documented contract value."""
    import validate as v

    python_codes = {
        getattr(v, name)
        for name in dir(v)
        if name.startswith("R_") and isinstance(getattr(v, name), str)
    }
    assert python_codes >= {
        R_TOPIC,
        R_JSON,
        R_SCHEMA,
        R_VALUE,
        R_UNIT,
        R_RANGE,
        R_TS_FUTURE,
        R_TS_OLD,
        R_TS_FORMAT,
        R_QUALITY,
        R_UNKNOWN_POINT,
    }


def test_contract_rules_match_the_python_implementation(validator, rules):
    assert validator.rules["topic_pattern"] == rules["topic_pattern"]
    assert validator.rules["payload_schema"]["required_fields"] == rules["payload_schema"]["required_fields"]
    assert validator.rules["max_value_abs"] == rules["max_value_abs"]
    assert validator.rules["max_future_skew_minutes"] == rules["max_future_skew_minutes"]
    assert validator.rules["max_past_age_hours"] == rules["max_past_age_hours"]
    assert validator.rules["rules_by_point_class"] == rules["rules_by_point_class"]


def test_flow_js_enforces_the_same_topic_pattern_as_the_contract(rules):
    """The flow's JS pattern is the contract pattern with JS group syntax."""
    nodes = {n["id"]: n for n in json.loads(FLOW_MERGED.read_text(encoding="utf-8"))}
    func = nodes["fn_parse"]["func"]
    match = re.search(r"const JS_TOPIC_PATTERN = (\".*?\");", func)
    assert match, "fn_parse no longer declares JS_TOPIC_PATTERN"
    js_pattern = json.loads(match.group(1))
    # (?P<name>...) in Python becomes (?<name>...) in JS; nothing else differs
    expected = re.sub(r"\(\?P<([a-z_]+)>", r"(?<\1>", rules["topic_pattern"])
    assert js_pattern == expected


def test_flow_js_uses_the_same_reason_codes(rules, registry):
    """A reason the JS never emits would mean the README overstates the checks."""
    nodes = {n["id"]: n for n in json.loads(FLOW_MERGED.read_text(encoding="utf-8"))}
    func = nodes["fn_parse"]["func"]
    emitted = set(re.findall(r"reject\('([A-Z_]+)'\)", func))
    assert emitted == {
        R_TOPIC,
        R_JSON,
        R_SCHEMA,
        R_VALUE,
        R_RANGE,
        R_TS_FORMAT,
        R_TS_FUTURE,
        R_TS_OLD,
        R_UNIT,
        R_QUALITY,
        R_UNKNOWN_POINT,
    }


def test_flow_reads_its_rules_from_the_contract_at_runtime():
    """Hard-coded thresholds in the flow would silently diverge from the contract."""
    nodes = {n["id"]: n for n in json.loads(FLOW_MERGED.read_text(encoding="utf-8"))}
    func = nodes["fn_parse"]["func"]
    assert "global.get('BMS_RULES')" in func
    for threshold in ("max_value_abs", "max_future_skew_minutes", "max_past_age_hours", "rules_by_point_class"):
        assert threshold in func


def test_semantic_check_ids_are_documented(rules):
    ids = {c["id"] for c in rules["semantic_checks"]}
    assert ids == {"SEM-01", "SEM-02", "SEM-03", "SEM-04", "SEM-05"}
    for check in rules["semantic_checks"]:
        assert check["description"].strip()
        assert check["severity"] in {"warning", "critical"}


# --------------------------------------------------------------------- accept
def test_valid_payload_is_accepted_and_normalised(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "room_temp")
    result = validator.check(row["topic"], payload(ts=START, value=21.4), now=START)
    assert result.ok
    assert result.point_id == row["point_id"]
    assert result.value == pytest.approx(21.4)
    assert result.unit == "C"
    assert result.quality == "good"


def test_unit_aliases_are_normalised_not_rejected(validator, registry):
    """Real controllers send degC; the contract must accept it and convert."""
    row = next(r for r in registry.values() if r["point_class"] == "room_temp")
    for alias in ("c", "degC", "°C", "Celsius"):
        result = validator.check(row["topic"], payload(ts=START, value=21.0, unit=alias), now=START)
        assert result.ok, alias
        assert result.unit == "C"


def test_fahrenheit_is_converted_to_celsius(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "room_temp")
    result = validator.check(row["topic"], payload(ts=START, value=69.8, unit="F"), now=START)
    assert result.ok
    assert result.value == pytest.approx(21.0, abs=0.01)


def test_to_celsius_helper():
    assert to_celsius(32.0, "F") == pytest.approx(0.0)
    assert to_celsius(21.0, "C") == 21.0
    assert normalise_unit(" KWH ") == "kWh"
    assert normalise_unit("nonsense") == "nonsense"


def test_quality_suspect_is_accepted_and_preserved(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "co2")
    result = validator.check(row["topic"], payload(ts=START, value=520, unit="ppm", quality="suspect"), now=START)
    assert result.ok
    assert result.quality == "suspect"


# --------------------------------------------------------------------- reject
@pytest.mark.parametrize(
    ("topic", "body", "reason"),
    [
        ("campus/B001/ahu", payload(), R_TOPIC),  # too few segments
        ("campus/X999/ahu/ahu_01/supply_temp", payload(), R_TOPIC),  # building not B\d{3}
        ("campus/B001/chiller/ahu_01/supply_temp", payload(), R_TOPIC),  # unknown system
        ("campus/B001/ahu/AHU_01/supply_temp", payload(), R_TOPIC),  # uppercase equipment
        ("campus/B001/ahu/ahu_01/supply_temp/extra", payload(), R_TOPIC),  # too many segments
    ],
)
def test_topic_pattern_rejects(validator, topic, body, reason):
    assert _check(validator, topic, body, now=START).reason == reason


def test_malformed_json_is_rejected(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    assert validator.check(row["topic"], "{not json", now=START).reason == R_JSON
    assert validator.check(row["topic"], b"\xff\xfe binary", now=START).reason == R_JSON


@pytest.mark.parametrize("field", ["ts", "value", "unit", "quality"])
def test_each_required_field_is_required(validator, registry, field):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    result = validator.check(row["topic"], payload(ts=START, value=13.0, drop=(field,)), now=START)
    assert result.reason == R_SCHEMA, field


def test_json_array_payload_is_rejected(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    assert validator.check(row["topic"], "[1,2,3]", now=START).reason == R_SCHEMA


@pytest.mark.parametrize("value", ["not_a_number", None, True, [1]])
def test_non_numeric_values_are_rejected(validator, registry, value):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    assert validator.check(row["topic"], payload(ts=START, value=value), now=START).reason == R_VALUE


def test_unknown_quality_is_rejected(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    result = validator.check(row["topic"], payload(ts=START, value=13.0, quality="excellent"), now=START)
    assert result.reason == R_QUALITY


def test_unit_mismatch_is_rejected(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    assert validator.check(row["topic"], payload(ts=START, value=13.0, unit="kWh"), now=START).reason == R_UNIT


def test_out_of_range_values_are_rejected(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    # contract range for supply_temp is -20..90 C
    assert validator.check(row["topic"], payload(ts=START, value=95.0), now=START).reason == R_RANGE
    assert validator.check(row["topic"], payload(ts=START, value=-40.0), now=START).reason == R_RANGE


def test_absurd_magnitude_is_rejected_even_within_the_class_range(validator, registry):
    """A stuck-at-garbage meter can report 99999 ppm 'valid'."""
    row = next(r for r in registry.values() if r["point_class"] == "co2")
    assert validator.check(row["topic"], payload(ts=START, value=999999, unit="ppm"), now=START).reason == R_RANGE


def test_unparseable_timestamp_is_rejected(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    result = validator.check(row["topic"], payload(ts="yesterday", value=13.0), now=START)
    assert result.reason == R_TS_FORMAT


def test_timestamp_too_far_in_the_future_is_rejected(validator, registry):
    """A clock-misconfigured controller must not write future rows."""
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    future = START + timedelta(minutes=30)
    assert validator.check(row["topic"], payload(ts=future, value=13.0), now=START).reason == R_TS_FUTURE


def test_small_clock_skew_is_tolerated(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    result = validator.check(row["topic"], payload(ts=START + timedelta(minutes=2), value=13.0), now=START)
    assert result.ok


def test_timestamp_older_than_the_age_budget_is_rejected(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    assert validator.check(row["topic"], payload(ts=START - timedelta(days=8), value=13.0), now=START).reason == R_TS_OLD


def test_unknown_point_id_is_rejected(validator):
    """A valid topic shape for a building/system pair nothing is registered on."""
    result = validator.check("campus/B009/ahu/ahu_01/supply_temp", payload(ts=START, value=13.0), now=START)
    assert result.reason == R_UNKNOWN_POINT


def test_checker_never_raises_on_hostile_input(validator):
    for hostile in ["", "null", "{}", '{"value": {"a": [1,2]}}', '{"ts": null}', "12"]:
        assert validator.check("campus/B001/ahu/ahu_01/supply_temp", hostile, now=START).ok is False


def test_z_suffix_timestamps_are_accepted(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    body = payload(ts=START, value=13.0).replace('+00:00', 'Z')
    assert validator.check(row["topic"], body, now=START).ok


def test_naive_timestamp_is_treated_as_utc(validator, registry):
    row = next(r for r in registry.values() if r["point_class"] == "supply_temp")
    body = json.dumps({"ts": "2026-10-07T23:00:00", "value": 13.0, "unit": "C", "quality": "good"})
    assert validator.check(row["topic"], body, now=START).ok


def test_parse_topic_returns_the_four_segments(validator):
    assert validator.parse_topic("campus/B007/pump/pump_03/sub_meter_kwh") == (
        "B007",
        "pump",
        "pump_03",
        "sub_meter_kwh",
    )
    assert validator.parse_topic("nonsense") is None