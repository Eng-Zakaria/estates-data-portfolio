"""Tests for P10 mapping layer."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mapping import INTERNAL_TO_RETURN, validate_mapping, get_return_category


def test_all_internal_categories_mapped():
    expected = {"Teaching", "Office", "Laboratory", "Library", "Residential", "Catering", "Sports", "Support"}
    assert set(INTERNAL_TO_RETURN.keys()) == expected


def test_mapping_is_injective():
    """Each internal category maps to exactly one return category."""
    counts = {}
    for internal, ret in INTERNAL_TO_RETURN.items():
        counts.setdefault(internal, 0)
        counts[internal] += 1
    for internal, count in counts.items():
        assert count == 1, f"Internal category {internal} has {count} mappings"


def test_validate_mapping():
    ok, errors = validate_mapping()
    assert ok, f"Mapping validation failed: {errors}"


def test_return_categories_expected():
    assert set(INTERNAL_TO_RETURN.values()) == {"Teaching", "Research", "Residential", "Other"}