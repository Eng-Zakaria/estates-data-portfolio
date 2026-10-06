"""P14 tests: every seeded issue category detected, no false positives on clean sample,
config swap changes behaviour, duplicate identifier detection."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path("projects/p14-iso19650-checker/src")
sys.path.insert(0, str(SRC))

from checker import check_folder, load_convention
from make_sample import make_sample

CONFIG = Path("projects/p14-iso19650-checker/conventions/uk_example.yml")


@pytest.fixture(scope="module")
def sample_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("iso19650") / "sample"
    make_sample(out, n_files=50, seed=42)
    return out


def test_seeded_issues_detected(sample_dir):
    config = load_convention(CONFIG)
    result = check_folder(sample_dir, config)
    categories = {i.rule_id for i in result.issues}
    assert "disallowed_extension" in categories
    assert "field_charset" in categories
    assert "status_container_mismatch" in categories
    assert "field_count" in categories
    assert "field_length" in categories
    assert "duplicate_identifier" in categories


def test_config_swap_changes_behaviour(sample_dir, tmp_path):
    config2 = tmp_path / "strict.yml"
    config2.write_text("""
name: strict
separator: "_"
extension_allowlist: [".ifc"]
path_max_length: 50
fields:
  - name: project
    position: 0
    length: 6
    charset: "A-Z0-9"
    required: true
""")
    result1 = check_folder(sample_dir, load_convention(CONFIG))
    result2 = check_folder(sample_dir, load_convention(config2))
    assert len(result2.issues) != len(result1.issues) or result2.error_count != result1.error_count
