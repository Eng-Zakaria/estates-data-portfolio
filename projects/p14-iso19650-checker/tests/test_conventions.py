"""Convention-agnosticism: swapping the config file changes behaviour with no code edit (spec
acceptance criterion), and the shipped configs are validated against their own provenance."""

from __future__ import annotations

import pytest
from checker import ConventionConfig, check_folder, load_convention, load_convention_text
from conftest import UK_CONVENTION, VARIANT_CONVENTION, write
from pydantic import ValidationError

BAD_CONVENTIONS = {
    "duplicate positions": """
name: bad
fields:
  - {name: a, position: 0}
  - {name: b, position: 0}
""",
    "fields out of position order": """
name: bad
fields:
  - {name: b, position: 1}
  - {name: a, position: 0}
""",
    "unknown id_fields reference": """
name: bad
id_fields: [a, missing]
fields:
  - {name: a, position: 0}
""",
    "unknown sequence field": """
name: bad
sequence: {field: nope}
fields:
  - {name: a, position: 0}
""",
    "multi-character separator": """
name: bad
separator: "--"
fields:
  - {name: a, position: 0}
""",
    "length and min/max together": """
name: bad
fields:
  - {name: a, position: 0, length: 2, min_length: 1}
""",
    "min greater than max": """
name: bad
fields:
  - {name: a, position: 0, min_length: 6, max_length: 2}
""",
    "unknown case policy": """
name: bad
case: mixed
fields:
  - {name: a, position: 0}
""",
}


@pytest.mark.parametrize("label,text", sorted(BAD_CONVENTIONS.items()))
def test_invalid_conventions_are_rejected(label, text):
    """A typo in a convention file must fail loudly at load time, not silently disable a rule."""
    with pytest.raises(ValidationError):
        load_convention_text(text)


def test_shipped_conventions_declare_their_source(uk_config, variant_config):
    """AGENTS.md rule 4: no code list without a recorded source."""
    for config in (uk_config, variant_config):
        assert config.source is not None
        assert config.source.name
        assert config.source.url.startswith("https://")
        assert config.source.retrieved


def test_uk_convention_matches_the_published_annex_tables(uk_config):
    """Field widths, code lists and the revision pattern, hand-checked against the Annex tables."""
    fields = {f.name: f for f in uk_config.fields}
    assert [f.name for f in uk_config.fields][:7] == [
        "project",
        "originator",
        "volume_system",
        "level_location",
        "type",
        "role",
        "number",
    ]
    assert (fields["project"].low, fields["project"].high) == (2, 6)
    assert (fields["originator"].low, fields["originator"].high) == (2, 6)
    assert (fields["volume_system"].low, fields["volume_system"].high) == (2, 2)
    assert (fields["role"].low, fields["role"].high) == (1, 2)
    assert (fields["number"].low, fields["number"].high) == (4, 6)
    assert fields["number"].charset == "0-9"

    # Annex Table 1.3 level/location codes
    assert fields["level_location"].allowed_values == ["ZZ", "XX", "00", "01", "02", "B1", "M1"]
    # Annex Table 1.4 type codes (28 published codes)
    assert len(fields["type"].allowed_values) == 28
    assert {
        "AF",
        "BQ",
        "CA",
        "CM",
        "CO",
        "CP",
        "CR",
        "DB",
        "DR",
        "FN",
        "HS",
        "IE",
        "M2",
        "M3",
        "MI",
        "MR",
        "MS",
        "PP",
        "PR",
        "RD",
        "RI",
        "RP",
        "SA",
        "SH",
        "SN",
        "SP",
        "SU",
        "VS",
    } == set(fields["type"].allowed_values)
    # Annex Table 1.5 discipline codes
    assert set(fields["role"].allowed_values) == set("ABCDEFGHIKLM PQSTWXYZ".replace(" ", ""))
    # Annex 2.1.1 revision: P/C + two integers, optional WIP version suffix
    assert fields["revision"].pattern == "[PC][0-9]{2}(\\.[0-9]{2})?"
    # Annex Table 2.2 / Part C statuses, and S7 is withdrawn so it is not accepted
    assert fields["status"].pattern == "S[0-6]|A[1-9][0-9]*|B[1-9][0-9]*|CR"
    assert uk_config.separator == "-"
    assert uk_config.container_states["WIP"] == ["S0"]


def test_variant_convention_is_a_different_shape(uk_config, variant_config):
    """The second shipped convention must actually differ, or it proves nothing."""
    assert variant_config.separator == "_" != uk_config.separator
    assert len(variant_config.fields) != len(uk_config.fields)
    assert [f.name for f in variant_config.fields][6] == "asset_class"
    assert variant_config.field_by_name("asset_class") is not None
    assert "asset_class" not in variant_config.id_field_names()
    assert variant_config.container_states["Shared"] == ["REV", "INFO"] != uk_config.container_states["Shared"]
    assert variant_config.metadata.enabled is False


def test_one_name_judged_by_two_conventions(tmp_path, uk_config, variant_config):
    """The same file, two conventions, two verdicts - no code edit between them."""
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")

    uk = check_folder(tmp_path, uk_config)
    variant = check_folder(tmp_path, variant_config)

    assert uk.error_count == 0
    assert variant.error_count > 0
    assert "illegal_character" in {i.rule_id for i in variant.issues}  # underscores are illegal here
    assert "field_length" in {i.rule_id for i in variant.issues}  # PRJ01 is not the variant's 5 chars


def test_same_folder_same_convention_is_deterministic(tmp_path, uk_config):
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0003-S0-P01.01.txt")
    first = check_folder(tmp_path, uk_config)
    second = check_folder(tmp_path, uk_config)
    assert [i.message for i in first.issues] == [i.message for i in second.issues]
    assert first.compliance_pct() == second.compliance_pct()


def test_convention_with_no_id_fields_falls_back_to_all_but_metadata(minimal_config):
    config = load_convention_text(
        """
name: fallback
separator: "-"
fields:
  - {name: project, position: 0}
  - {name: status, position: 1}
  - {name: revision, position: 2}
"""
    )
    assert config.id_field_names() == ["project"]


def test_shipped_conventions_load_from_disk():
    assert load_convention(UK_CONVENTION).name == "uk_national_annex"
    assert load_convention(VARIANT_CONVENTION).name == "estates_cde_variant"
    assert isinstance(load_convention(UK_CONVENTION), ConventionConfig)
