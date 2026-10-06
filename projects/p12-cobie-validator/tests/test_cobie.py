"""P12 tests: each rule type, seeded-error recall, AIR edit, loader idempotency."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path("projects/p12-cobie-validator/src")
sys.path.insert(0, str(SRC))

# ruff: noqa: E402
from loader import load_workbook_to_staging
from make_sample_cobie import make_corrupted_cobie, make_valid_cobie
from spec import load_rules
from validate import validate_workbook

RULES = Path("projects/p12-cobie-validator/rules/cobie.yml")
AIR = Path("projects/p12-cobie-validator/rules/air.yml")


@pytest.fixture(scope="module")
def valid_path(tmp_path_factory):
    out = tmp_path_factory.mktemp("cobie") / "valid.xlsx"
    make_valid_cobie(out)
    return out


@pytest.fixture(scope="module")
def corrupted_bundle(tmp_path_factory):
    out = tmp_path_factory.mktemp("cobie") / "corrupted.xlsx"
    seeded = make_corrupted_cobie(out)
    return out, seeded


def _result(path):
    return validate_workbook(path, load_rules(RULES), load_rules(AIR))


def test_valid_workbook_zero_blocking(valid_path):
    result = _result(valid_path)
    assert result.blocking_count == 0
    assert result.warning_count == 0
    assert result.score == 100.0


def test_seeded_event_count_at_least_40(corrupted_bundle):
    _, seeded = corrupted_bundle
    assert len(seeded) >= 40


def test_missing_sheets_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    issues = [i for i in _result(path).issues if i.rule_id.startswith("sheet_")]
    sheets = {i.sheet for i in issues}
    assert {"Zone", "Document"} <= sheets


def test_missing_columns_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    ids = {i.rule_id for i in _result(path).issues}
    assert "col_contact_phone" in ids
    assert "col_type_model" in ids


def test_column_order_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    ids = {i.rule_id for i in _result(path).issues}
    assert "order_component_cols" in ids


def test_mandatory_and_duplicates_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    ids = {i.rule_id for i in _result(path).issues}
    assert "mandatory_space_floorname" in ids
    assert "unique_component_name" in ids
    assert "unique_type_name" in ids
    assert "unique_component_serial" in ids


def test_fk_broken_and_multivalue_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    issues = [i for i in _result(path).issues if i.rule_id.startswith("fk_")]
    assert len(issues) >= 5
    assert any("Ghost-99" in i.message for i in issues)


def test_createdby_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    issues = [i for i in _result(path).issues if i.rule_id == "createdby_in_contact"]
    assert len(issues) >= 2


def test_format_email_and_date_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    issues = _result(path).issues
    assert any(i.rule_id == "format_contact_email" for i in issues)
    assert any(i.rule_id == "format_component_installdate" for i in issues)


def test_numeric_range_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    issues = [i for i in _result(path).issues if i.rule_id.startswith("range_")]
    assert len(issues) >= 4


def test_category_pattern_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    issues = [i for i in _result(path).issues if i.rule_id.startswith("category_")]
    assert len(issues) >= 3


def test_air_missing_attribute_detected(corrupted_bundle):
    path, _ = corrupted_bundle
    issues = [i for i in _result(path).issues if i.rule_id.startswith("air_")]
    assert len(issues) >= 5


def test_corrupted_score_below_valid(corrupted_bundle, valid_path):
    assert _result(corrupted_bundle[0]).score < _result(valid_path).score
    assert _result(corrupted_bundle[0]).blocking_count > 0


def test_air_edit_changes_results_without_code_change(corrupted_bundle):
    path, _ = corrupted_bundle
    full = validate_workbook(path, load_rules(RULES), load_rules(AIR))
    trimmed = [r for r in load_rules(AIR) if r["id"] != "air_manufacturer_required"]
    fewer = validate_workbook(path, load_rules(RULES), trimmed)
    assert fewer.warning_count < full.warning_count


def test_loader_valid_inserts_and_idempotent(valid_path, tmp_path):
    out = tmp_path / "handover"
    first = load_workbook_to_staging(valid_path, out, truth_assets=None)
    assert first["counts"]["inserted"] == 8
    assert first["counts"]["rejected"] == 0
    assert (out / "staging_components.csv").exists()
    assert (out / "quarantine.csv").exists()
    assert (out / "audit.json").exists()
    second = load_workbook_to_staging(valid_path, out, truth_assets=None)
    assert second["counts"]["unchanged"] == 8
    assert second["counts"]["inserted"] == 0


def test_loader_corrupted_rejects_with_reasons(corrupted_bundle, tmp_path):
    path, _ = corrupted_bundle
    res = load_workbook_to_staging(path, tmp_path / "handover_bad", truth_assets=None)
    assert res["counts"]["rejected"] > 0
    assert all(q["reasons"] for q in res["quarantine"])


def test_loader_dry_run_writes_nothing(valid_path, tmp_path):
    out = tmp_path / "dry"
    res = load_workbook_to_staging(valid_path, out, truth_assets=None, dry_run=True)
    assert res["counts"]["inserted"] == 8
    assert not out.exists()
    assert "inserted=8" in res["diff"]
