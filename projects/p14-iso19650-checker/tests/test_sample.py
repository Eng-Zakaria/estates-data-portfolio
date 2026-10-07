"""Acceptance tests against the generated sample project (spec acceptance criteria).

1. every seeded issue category is detected;
2. false positives = 0 on the clean sample, for both shipped conventions;
3. the seeded series gaps are the gaps the checker reports;
4. the sample generator is deterministic (same seed, same tree).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from checker import check_folder, load_convention
from conftest import UK_CONVENTION, VARIANT_CONVENTION
from make_sample import make_sample

SEED = 42
N_FILES = 300


@pytest.fixture(scope="module")
def seeded(tmp_path_factory):
    root = tmp_path_factory.mktemp("p14-seeded")
    out = root / "sample"
    truth = make_sample(out, n_files=N_FILES, seed=SEED, config_path=UK_CONVENTION)
    return out, truth


@pytest.fixture(scope="module")
def seeded_result(seeded):
    out, truth = seeded
    return check_folder(out, load_convention(UK_CONVENTION), register=Path(truth["register"]))


def test_every_seeded_category_is_detected(seeded, seeded_result):
    """For each planted file, every rule it was planted with is reported against that file."""
    out, truth = seeded
    by_path: dict[str, set[str]] = {}
    for issue in seeded_result.issues:
        by_path.setdefault(issue.path, set()).add(issue.rule_id)

    missed: list[tuple[str, str]] = []
    planted_files = 0
    for entry in truth["files"]:
        if not entry["seeded_rule_ids"]:
            continue
        planted_files += 1
        found = by_path.get(entry["path"], set())
        for rule in entry["seeded_rule_ids"]:
            if rule not in found:
                missed.append((entry["path"], rule))
    assert missed == []
    assert planted_files >= 15


def test_all_expected_rule_categories_fire(seeded_result):
    """Guards against a seed silently ceasing to be planted."""
    expected = {
        "field_count",
        "field_missing",
        "field_length",
        "field_charset",
        "field_allowed_values",
        "field_pattern",
        "field_case",
        "illegal_character",
        "separator_misuse",
        "empty_field",
        "revision_format",
        "disallowed_extension",
        "status_container_mismatch",
        "duplicate_identifier",
        "metadata_mismatch",
        "orphan_file",
        "number_gap",
        "revision_gap",
        "path_length",
        "stem_length",
    }
    assert expected <= set(seeded_result.by_rule())


def test_seeded_series_gaps_are_reported_exactly(seeded, seeded_result):
    out, truth = seeded
    for gap in truth["series_gaps"]:
        messages = [i.message for i in seeded_result.issues if i.rule_id == gap["rule_id"]]
        for missing in gap["missing"]:
            assert any(f"{missing} is missing" in m for m in messages), (
                f"expected {gap['rule_id']} for missing {missing}, got {messages}"
            )


def test_seed_is_recorded_and_severity_split_is_sane(seeded_result):
    assert seeded_result.error_count > 0
    assert seeded_result.warning_count > 0
    assert seeded_result.files_with_errors <= seeded_result.total_files


def test_false_positives_are_zero_on_the_clean_sample(tmp_path, uk_config):
    """Acceptance: zero false positives on a compliant sample."""
    out = tmp_path / "clean"
    truth = make_sample(out, n_files=200, seed=SEED, clean=True, config_path=UK_CONVENTION)
    result = check_folder(out, uk_config, register=Path(truth["register"]))
    assert result.total_files == truth["counts"]["total"]
    assert result.issues == []
    assert result.compliance_pct() == 100.0


def test_false_positives_are_zero_for_the_second_convention(tmp_path, variant_config):
    """The other convention's clean sample must also be clean - no rules hard-coded to the UK config."""
    out = tmp_path / "variant"
    truth = make_sample(out, n_files=120, seed=SEED, clean=True, config_path=VARIANT_CONVENTION)
    result = check_folder(out, variant_config, register=Path(truth["register"]))
    assert result.issues == []
    assert result.total_files == truth["counts"]["total"] == 120


def test_generator_is_deterministic(tmp_path):
    first = tmp_path / "a"
    second = tmp_path / "b"
    make_sample(first, n_files=40, seed=SEED, clean=True, config_path=UK_CONVENTION)
    make_sample(second, n_files=40, seed=SEED, clean=True, config_path=UK_CONVENTION)
    names_a = sorted(p.relative_to(first).as_posix() for p in first.rglob("*") if p.is_file())
    names_b = sorted(p.relative_to(second).as_posix() for p in second.rglob("*") if p.is_file())
    assert names_a == names_b

    different = tmp_path / "c"
    make_sample(different, n_files=40, seed=SEED + 1, clean=True, config_path=UK_CONVENTION)
    names_c = sorted(p.relative_to(different).as_posix() for p in different.rglob("*") if p.is_file())
    assert names_a != names_c


def test_truth_file_is_self_describing(seeded):
    _, truth = seeded
    payload = json.loads(json.dumps(truth))
    assert payload["convention"] == "uk_national_annex"
    assert payload["seed"] == SEED
    assert payload["counts"]["total"] == payload["counts"]["compliant"] + payload["counts"]["seeded"]
    assert len(payload["orphans"]) == payload["counts"]["orphans"] == 1
    assert {gap["rule_id"] for gap in payload["series_gaps"]} == {"number_gap", "revision_gap"}


def test_orphan_seed_is_only_reported_against_the_supplied_register(seeded):
    out, truth = seeded
    config = load_convention(UK_CONVENTION)
    without_register = check_folder(out, config)
    assert "orphan_file" not in {i.rule_id for i in without_register.issues}
    with_register = check_folder(out, config, register=Path(truth["register"]))
    orphans = [i.path for i in with_register.issues if i.rule_id == "orphan_file"]
    assert orphans == truth["orphans"]
