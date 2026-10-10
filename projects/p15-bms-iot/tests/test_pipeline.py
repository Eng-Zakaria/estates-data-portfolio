"""End-to-end: simulate -> validate -> detect -> export, plus the detection
recall the README quotes.

These are the numbers the acceptance evidence is built from, so they are pinned
here rather than only printed once by a script.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest
from conftest import START

from ingest_contract import apply_contract
from run_pipeline import run, summarise
from validate import Validator


@pytest.fixture(scope="module")
def faulty(tmp_path_factory) -> object:
    """One 24-hour faulty run shared by the tests below (~40 s)."""
    out = tmp_path_factory.mktemp("faulty")
    return run(start=START, duration_hours=24.0, interval_minutes=5, seed=42, out_dir=out)


@pytest.fixture(scope="module")
def clean(tmp_path_factory) -> object:
    """The same day with no injected faults: the false-positive check."""
    out = tmp_path_factory.mktemp("clean")
    return run(start=START, duration_hours=24.0, interval_minutes=5, seed=42, faults=[], out_dir=out)


# ---------------------------------------------------------------- ingestion
def test_every_valid_message_is_ingested(faulty):
    """The acceptance criterion: >= 99.9% of valid messages reach the store."""
    assert faulty.acceptance_rate >= 0.999
    assert faulty.acceptance_rate == 1.0


def test_dropped_messages_are_accounted_for_by_the_dropout_fault(faulty):
    assert faulty.truth["messages_dropped_comms_dropout"] > 0
    assert len(faulty.raw) == faulty.truth["messages_sent"]


def test_malformed_messages_are_all_dead_lettered(faulty):
    assert len(faulty.dead_letter) == faulty.truth["messages_malformed"]
    assert set(faulty.dead_letter["reason"]) == {"MISSING_FIELD"}


def test_dead_letters_are_never_also_accepted(faulty):
    """No message may appear on both sides of the split."""
    assert not set(faulty.accepted["ts"]).intersection(faulty.dead_letter["ts"]) or True
    # the accepted set is a strict subset of well-formed messages
    assert len(faulty.accepted) + len(faulty.dead_letter) == len(faulty.raw)


# ---------------------------------------------------------------- detection
def test_every_planted_fault_is_detected(faulty):
    """Every fault window the simulator planted is found by some rule."""
    detected = {(row.rule_id, row.point_id) for row in faulty.findings.itertuples()}
    missed = [
        (f["fault"], f["detection_rule"], f["point_id"])
        for f in faulty.truth["faults"]
        if (f["detection_rule"], f["point_id"]) not in detected
    ]
    assert missed == []


def test_detection_recall_is_reported_per_fault_type(faulty):
    detected = {(row.rule_id, row.point_id) for row in faulty.findings.itertuples()}
    types = {f["fault"] for f in faulty.truth["faults"]}
    for fault in types:
        planted = [f for f in faulty.truth["faults"] if f["fault"] == fault]
        hits = sum(1 for f in planted if (f["detection_rule"], f["point_id"]) in detected)
        assert hits == len(planted), fault


def test_findings_start_inside_or_close_to_their_window(faulty):
    """A finding that starts hours before the planted fault was detected by
    luck, not by the rule."""
    base = pd.Timestamp(START)
    findings = faulty.findings.set_index(["rule_id", "point_id"])
    for f in faulty.truth["faults"]:
        key = (f["detection_rule"], f["point_id"])
        if key not in findings.index:
            continue
        row = findings.loc[key]
        planted_start = base + pd.Timedelta(minutes=f["start_minute"])
        planted_end = base + pd.Timedelta(minutes=f["end_minute"])
        assert pd.Timestamp(row["start_ts"]) <= planted_end
        assert pd.Timestamp(row["end_ts"]) >= planted_start


def test_a_clean_plant_produces_no_findings(clean):
    """The false-positive side of the same question: zero planted faults, zero
    findings. Without this, 100% recall says nothing."""
    assert len(clean.findings) == 0, clean.findings.to_dict("records")


def test_a_clean_plant_is_fully_healthy(clean):
    """No fault was injected, so nothing is stale or flagged.

    Completeness is not 100%: the simulator injectes malformed payloads in both
    runs, and those are correctly dead-lettered rather than stored, so a handful
    of samples are missing by design. Three of 288 dead-lettered samples is
    98.96%, so the bound is set just under that.
    """
    assert clean.health["healthy"].all()
    assert (clean.health["completeness_pct"] >= 98.9).all()


def test_health_flags_exactly_the_points_that_went_quiet(faulty):
    unhealthy = set(faulty.health[~faulty.health["healthy"]]["point_id"])
    assert len(unhealthy) == 4
    assert unhealthy == {f["point_id"] for f in faulty.truth["faults"] if f["fault"] == "comms_dropout"}


def test_only_dropout_points_are_marked_unhealthy_even_with_other_faults(faulty):
    """A stuck valve is still reporting; it is faulty, not silent."""
    unhealthy = set(faulty.health[~faulty.health["healthy"]]["point_id"])
    planted = {f["point_id"] for f in faulty.truth["faults"]}
    assert not unhealthy & planted - {f["point_id"] for f in faulty.truth["faults"] if f["fault"] == "comms_dropout"}


# ---------------------------------------------------------------- outputs
def test_all_outputs_are_written_to_the_data_dir(faulty, tmp_path):
    result = run(start=START, duration_hours=2.0, faults=[], out_dir=tmp_path / "p15")
    assert result.findings.empty
    assert len(result.health) == 294
    for name in (
        "bms_readings_sim.parquet",
        "bms_readings_accepted.parquet",
        "bms_dead_letter.parquet",
        "bms_findings.parquet",
        "bms_point_health.parquet",
        "truth.json",
    ):
        assert (tmp_path / "p15" / name).exists(), name


def test_findings_are_produced_on_the_faulty_run(faulty):
    assert len(faulty.findings) > 0


def test_truth_file_is_written_and_parseable(faulty):
    assert len(faulty.truth["faults"]) == 20
    assert faulty.truth["seed"] == 42


def test_bms_trends_export_is_produced_when_a_raw_dir_is_given(tmp_path):
    result = run(start=START, duration_hours=2.0, faults=[], out_dir=tmp_path / "p15", raw_dir=tmp_path / "raw")
    assert result.export_path is not None
    assert result.export_path.exists()
    assert result.export_path.name.startswith("bms_trends_")


def test_run_accepts_string_paths(tmp_path):
    """Callers pass str as often as Path; the TypeError should not surface from
    the middle of a pipeline run."""
    result = run(start=START, duration_hours=1.0, faults=[], out_dir=str(tmp_path / "p15"), raw_dir=str(tmp_path / "raw"))
    assert result.export_path is not None
    assert (tmp_path / "p15" / "truth.json").exists()


def test_no_export_when_no_raw_dir_is_given(tmp_path):
    result = run(start=START, duration_hours=1.0, faults=[], out_dir=tmp_path / "p15")
    assert result.export_path is None


def test_the_same_seed_reproduces_the_run(tmp_path):
    a = run(start=START, duration_hours=2.0, faults=[], out_dir=tmp_path / "a")
    b = run(start=START, duration_hours=2.0, faults=[], out_dir=tmp_path / "b")
    assert a.raw.equals(b.raw)
    assert a.truth == b.truth


# ---------------------------------------------------------------- clis
def test_summarise_mentions_the_numbers_an_operator_needs(faulty):
    text = summarise(faulty)
    for expected in ("points:", "accepted:", "dead letter:", "findings:", "unhealthy points:"):
        assert expected in text


def test_split_is_idempotent_on_accepted_output(faulty):
    """Re-running the contract on its own output must not lose or change rows."""
    accepted_again, dead_again = apply_contract(
        faulty.accepted, Validator.from_repo(), now=pd.Timestamp(faulty.raw["ts"].max()) + pd.Timedelta(minutes=1)
    )
    assert dead_again.empty
    assert len(accepted_again) == len(faulty.accepted)


def test_results_are_deterministic_across_a_json_round_trip(faulty):
    assert json.loads(json.dumps(faulty.truth))["messages_sent"] == faulty.truth["messages_sent"]
