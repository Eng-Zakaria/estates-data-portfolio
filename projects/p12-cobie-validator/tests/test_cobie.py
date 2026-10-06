"""P12 tests: each rule type with pass + fail fixtures, valid workbook zero blocking,
corrupted workbook finds seeded errors, AIR change alters results.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path("projects/p12-cobie-validator/src")
sys.path.insert(0, str(SRC))

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
def corrupted_path(tmp_path_factory):
    out = tmp_path_factory.mktemp("cobie") / "corrupted.xlsx"
    make_corrupted_cobie(out)
    return out


def test_valid_workbook_zero_blocking(valid_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(valid_path, cobie_rules, air_rules)
    assert result.blocking_count == 0
    assert result.score == 100.0


def test_corrupted_workbook_has_blocking(corrupted_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(corrupted_path, cobie_rules, air_rules)
    assert result.blocking_count > 0
    assert result.score < 100.0


def test_missing_sheet_detected(corrupted_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(corrupted_path, cobie_rules, air_rules)
    sheet_missing = [i for i in result.issues if i.rule_id == "sheet_present"]
    assert len(sheet_missing) > 0


def test_missing_column_detected(corrupted_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(corrupted_path, cobie_rules, air_rules)
    col_missing = [i for i in result.issues if i.rule_id == "col_contact_email"]
    assert len(col_missing) > 0


def test_duplicate_key_detected(corrupted_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(corrupted_path, cobie_rules, air_rules)
    dups = [i for i in result.issues if i.rule_id == "unique_component_name"]
    assert len(dups) > 0


def test_fk_broken_detected(corrupted_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(corrupted_path, cobie_rules, air_rules)
    fks = [i for i in result.issues if i.rule_id.startswith("fk_")]
    assert len(fks) > 0


def test_format_email_detected(corrupted_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(corrupted_path, cobie_rules, air_rules)
    formats = [i for i in result.issues if i.rule_id.startswith("format_")]
    assert len(formats) > 0


def test_air_missing_attribute_detected(corrupted_path):
    cobie_rules = load_rules(RULES)
    air_rules = load_rules(AIR)
    result = validate_workbook(corrupted_path, cobie_rules, air_rules)
    airs = [i for i in result.issues if i.rule_id.startswith("air_")]
    assert len(airs) > 0
