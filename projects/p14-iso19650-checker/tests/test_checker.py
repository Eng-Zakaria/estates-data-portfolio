"""Rule-level tests with hand-checked fixtures (AGENTS.md rule 8: tests first for validators)."""

from __future__ import annotations

from checker import (
    CheckResult,
    _facet_key,
    _parse_revision,
    check_file,
    check_folder,
    compliance_summary,
    container_register,
    container_state_for,
    load_convention_text,
    parse_stem,
    status_allowed,
)
from conftest import register_outside, write


def rules(issues) -> set[str]:
    return {issue.rule_id for issue in issues}


def fields(issues, rule: str) -> set[str]:
    return {issue.field for issue in issues if issue.rule_id == rule}


# --- structural rules -------------------------------------------------------------
def test_compliant_name_has_no_issues(tmp_path, minimal_config):
    path = write(tmp_path, "WIP/PRJ1-DR-0001-S0.txt")
    issues, suggested = check_file(path, minimal_config, "WIP", "WIP/PRJ1-DR-0001-S0.txt")
    assert issues == []
    assert suggested is None


def test_field_count_only_flags_too_many_fields(minimal_config, tmp_path):
    """Annex fields 'can be shortened or expanded as required', so extra fields are not an error
    when every declared field is present; a missing declared field is (field_missing)."""
    short = write(tmp_path, "WIP/PRJ1-DR.txt")
    issues, _ = check_file(short, minimal_config, "WIP", "WIP/PRJ1-DR.txt")
    assert rules(issues) == {"field_missing"}
    assert fields(issues, "field_missing") == {"number", "status"}

    long = write(tmp_path, "WIP/PRJ1-DR-0001-S0-EXTRA.txt")
    issues, _ = check_file(long, minimal_config, "WIP", "WIP/PRJ1-DR-0001-S0-EXTRA.txt")
    assert "field_missing" not in rules(issues)


def test_field_length_bounds(tmp_path, minimal_config):
    short = write(tmp_path, "WIP/P-DR-0001-S0.txt")
    issues, _ = check_file(short, minimal_config, "WIP", "WIP/P-DR-0001-S0.txt")
    assert fields(issues, "field_length") == {"project"}
    assert "expected length 4, got 1" in [i.message for i in issues if i.rule_id == "field_length"][0]

    long = write(tmp_path, "WIP/PRJ1X-DR-0001-S0.txt")
    issues, _ = check_file(long, minimal_config, "WIP", "WIP/PRJ1X-DR-0001-S0.txt")
    assert fields(issues, "field_length") == {"project"}


def test_charset_pattern_and_code_list(tmp_path, minimal_config):
    digit_kind = write(tmp_path, "WIP/PRJ1-11-0001-S0.txt")
    issues, _ = check_file(digit_kind, minimal_config, "WIP", "WIP/PRJ1-11-0001-S0.txt")
    assert fields(issues, "field_charset") == {"kind"}

    bad_status = write(tmp_path, "WIP/PRJ1-DR-0001-S9.txt")
    issues, _ = check_file(bad_status, minimal_config, "WIP", "WIP/PRJ1-DR-0001-S9.txt")
    assert fields(issues, "field_pattern") == {"status"}

    bad_code = write(tmp_path, "WIP/PRJ1-XX-0001-S0.txt")
    issues, _ = check_file(bad_code, minimal_config, "WIP", "WIP/PRJ1-XX-0001-S0.txt")
    assert fields(issues, "field_allowed_values") == {"kind"}
    assert "DR, RP" in [i.message for i in issues if i.rule_id == "field_allowed_values"][0]


def test_case_is_a_warning_with_a_suggested_fix(tmp_path, minimal_config):
    path = write(tmp_path, "WIP/prj1-dr-0001-s0.txt")
    issues, suggested = check_file(path, minimal_config, "WIP", "WIP/prj1-dr-0001-s0.txt")
    case = [i for i in issues if i.rule_id == "field_case"]
    assert case and all(i.severity == "warning" for i in case)
    assert suggested == "PRJ1-DR-0001-S0"


def test_illegal_character_and_empty_field(tmp_path, minimal_config):
    spaced = write(tmp_path, "WIP/PRJ1 DR 0001 S0.txt")
    issues, _ = check_file(spaced, minimal_config, "WIP", "WIP/PRJ1 DR 0001 S0.txt")
    # a space that separates exactly the expected fields is a separator slip, not a stray character
    assert "separator_misuse" in rules(issues)

    stray = write(tmp_path, "WIP/PRJ1-DR-0001-S0 EXTRA.txt")
    issues, _ = check_file(stray, minimal_config, "WIP", "WIP/PRJ1-DR-0001-S0 EXTRA.txt")
    assert "illegal_character" in rules(issues)
    assert "separator_misuse" not in rules(issues)

    empty = write(tmp_path, "WIP/PRJ1--0001-S0.txt")
    issues, _ = check_file(empty, minimal_config, "WIP", "WIP/PRJ1--0001-S0.txt")
    assert "empty_field" in rules(issues)
    assert fields(issues, "empty_field") == {"kind"}


def test_extension_and_path_hygiene(tmp_path, minimal_config):
    exe = write(tmp_path, "WIP/PRJ1-DR-0001-S0.exe")
    issues, _ = check_file(exe, minimal_config, "WIP", "WIP/PRJ1-DR-0001-S0.exe")
    assert rules(issues) == {"disallowed_extension"}

    long_display = "/".join(["WIP"] + ["A" * 40, "B" * 40, "C" * 40, "PRJ1-DR-0001-S0.txt"])
    deep = write(tmp_path, long_display)
    issues, _ = check_file(deep, minimal_config, "WIP", long_display)
    assert "path_length" in rules(issues)

    long_stem = write(tmp_path, "WIP/PRJ1-DR-0001-S0-PADDINGPADDINGPADDING.txt")
    issues, _ = check_file(long_stem, minimal_config, "WIP", long_stem.name)
    assert "stem_length" in rules(issues)


# --- semantic rules ---------------------------------------------------------------
def test_status_must_match_container_state(tmp_path, minimal_config):
    ok = write(tmp_path, "WIP/PRJ1-DR-0001-S0.txt")
    assert check_file(ok, minimal_config, "WIP", "WIP/PRJ1-DR-0001-S0.txt")[0] == []

    wrong = write(tmp_path, "WIP/PRJ1-DR-0002-S4.txt")
    issues, _ = check_file(wrong, minimal_config, "WIP", "WIP/PRJ1-DR-0002-S4.txt")
    assert rules(issues) == {"status_container_mismatch"}

    # a folder that is not a state folder means no state rule applies
    loose = write(tmp_path, "Loose/PRJ1-DR-0003-S4.txt")
    assert check_file(loose, minimal_config, None, "Loose/PRJ1-DR-0003-S4.txt")[0] == []


def test_status_glob_matching(uk_config):
    """Published statuses A1..An and B1..Bn are open-ended, so the config uses a glob."""
    assert status_allowed("A1", ["A*"])
    assert status_allowed("A12", ["A*"])
    assert not status_allowed("S0", ["A*", "B*"])
    assert status_allowed("S3", ["S1", "S2", "S3", "S4", "S5", "S6"])
    assert uk_config.container_states["Published"] == ["A*", "B*"]


def test_duplicate_identifier_is_scoped_to_state_and_revision(tmp_path, uk_config):
    """Same id in two states = container lifecycle. Same id + revision in one state = a real duplicate."""
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    write(tmp_path, "Shared/PRJ01-ESTM-ZZ-01-DR-A-0001-S1-P01.txt")  # different state, different revision
    result = check_folder(tmp_path, uk_config)
    assert "duplicate_identifier" not in rules(result.issues)

    # ZCopy sorts last, so the copy is the file reported as the duplicate
    write(tmp_path, "WIP/ZCopy/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    result = check_folder(tmp_path, uk_config)
    duplicates = [i for i in result.issues if i.rule_id == "duplicate_identifier"]
    assert len(duplicates) == 1
    assert duplicates[0].path == "WIP/ZCopy/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt"
    assert "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt" in duplicates[0].message


def test_revision_format_parsing(uk_config):
    assert _parse_revision("P01", uk_config) == ("P", 1, None)
    assert _parse_revision("C02", uk_config) == ("C", 2, None)
    assert _parse_revision("P01.01", uk_config) == ("P", 1, 1)
    for bad in ("X1", "P1", "P001", "01", "P01.1", "P01.01.01"):
        assert _parse_revision(bad, uk_config) is None, bad


def test_version_suffix_can_be_switched_off():
    config = load_convention_text(
        """
name: no_suffix
separator: "-"
fields:
  - {name: number, position: 0, length: 2}
  - {name: revision, position: 1, pattern: "[PC][0-9]{2}(\\\\.[0-9]{2})?"}
revision: {field: revision, allow_version_suffix: false}
"""
    )
    assert _parse_revision("P01", config) == ("P", 1, None)
    assert _parse_revision("P01.01", config) is None


def test_number_gap_is_scoped_to_the_folder(tmp_path, uk_config):
    """Regression test: one series split across two folders is not a gap; a gap inside a folder is."""
    write(tmp_path, "WIP/A/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    write(tmp_path, "WIP/B/PRJ01-ESTM-ZZ-01-DR-A-0003-S0-P01.01.txt")
    result = check_folder(tmp_path, uk_config)
    assert not [i for i in result.issues if i.rule_id == "number_gap"]

    write(tmp_path, "WIP/A/PRJ01-ESTM-ZZ-01-DR-A-0005-S0-P01.01.txt")
    result = check_folder(tmp_path, uk_config)
    gaps = [i for i in result.issues if i.rule_id == "number_gap"]
    missing = [i.message.rsplit("number ", 1)[-1].split(" ")[0] for i in gaps]
    assert sorted(missing) == ["0002", "0003", "0004"]  # folder A holds 0001 and 0005 only
    assert all("WIP/A" in i.container_id for i in gaps)
    assert gaps[0].severity == "warning"


def test_revision_gap_keeps_preliminary_and_contractual_apart(tmp_path, uk_config):
    write(tmp_path, "Archive/PRJ01-ESTM-ZZ-01-DR-A-0001-CR-P01.txt")
    write(tmp_path, "Archive/PRJ01-ESTM-ZZ-01-DR-A-0001-CR-P03.txt")
    write(tmp_path, "Archive/PRJ01-ESTM-ZZ-01-DR-A-0002-CR-C01.txt")
    result = check_folder(tmp_path, uk_config)
    gaps = [i for i in result.issues if i.rule_id == "revision_gap"]
    assert len(gaps) == 1
    assert "P revision" in gaps[0].message and "02 is missing" in gaps[0].message


def test_orphan_file_against_supplied_register(tmp_path, uk_config):
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0002-S0-P01.01.txt")
    register = register_outside(tmp_path)
    register.write_text("path,container_id\nWIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt,x\n", encoding="utf-8")

    result = check_folder(tmp_path, uk_config, register=register)
    orphans = [i for i in result.issues if i.rule_id == "orphan_file"]
    assert [i.path for i in orphans] == ["WIP/PRJ01-ESTM-ZZ-01-DR-A-0002-S0-P01.01.txt"]

    missing = check_folder(tmp_path, uk_config, register=register_outside(tmp_path, "nope.csv"))
    assert "register_missing" in rules(missing.issues)


def test_metadata_mismatch_uses_the_documents_own_title(tmp_path, uk_config):
    honest = write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt", "DR 0001 ESTM ZZ site plan\n")
    assert check_file(honest, uk_config, "WIP", "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")[0] == []

    write(tmp_path, "WIP/PRJ01-ENGG-ZZ-01-DR-A-0002-S0-P01.01.txt", "Site walkaround notes\n")
    result = check_folder(tmp_path, uk_config)
    issues = [i for i in result.issues if i.rule_id == "metadata_mismatch"]
    assert fields(issues, "metadata_mismatch") == {"originator", "number"}
    assert all(i.severity == "error" for i in issues)


def test_metadata_check_is_skipped_when_the_name_does_not_parse(tmp_path, uk_config):
    """A name with an empty field must not also be accused of a title mismatch caused by that fault."""
    write(tmp_path, "WIP/PRJ01--ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt", "nothing relevant here\n")
    result = check_folder(tmp_path, uk_config)
    assert "metadata_mismatch" not in rules(result.issues)
    assert "empty_field" in rules(result.issues)


def test_metadata_can_be_switched_off(tmp_path, uk_config):
    config = uk_config.model_copy(update={"metadata": uk_config.metadata.model_copy(update={"enabled": False})})
    write(tmp_path, "WIP/PRJ01-ENGG-ZZ-01-DR-A-0007-S0-P01.01.txt", "unrelated title\n")
    result = check_folder(tmp_path, config)
    assert "metadata_mismatch" not in rules(result.issues)


# --- registers, summaries, helpers --------------------------------------------------
def test_container_register_records_facets_and_hashes(tmp_path, uk_config):
    write(tmp_path, "Shared/ZoneA/PRJ01-ESTM-ZZ-01-DR-A-0001-S1-P01.txt")
    rows = container_register(tmp_path, uk_config)
    assert len(rows) == 1
    row = rows[0]
    assert row["path"] == "Shared/ZoneA/PRJ01-ESTM-ZZ-01-DR-A-0001-S1-P01.txt"
    assert row["container_id"] == "PRJ01-ESTM-ZZ-01-DR-A-0001"
    assert row["originator"] == "ESTM"
    assert row["status"] == "S1"
    assert row["revision"] == "P01"
    assert row["state"] == "Shared"
    assert len(row["sha256"]) == 64


def test_compliance_summary_covers_field_folder_and_originator(tmp_path, uk_config):
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0002-S4-P01.01.txt")  # S4 is not valid in WIP
    write(tmp_path, "Shared/PRJ01-ENGG-ZZ-01-DR-A-0001-S1-P01.txt")
    result = check_folder(tmp_path, uk_config)
    rows = compliance_summary(tmp_path, uk_config, result)
    by_dimension = {row["dimension"]: {r["key"]: r for r in rows if r["dimension"] == row["dimension"]} for row in rows}

    assert by_dimension["overall"]["all"]["files"] == "3"
    assert by_dimension["field"]["status"]["errors"] == "1"
    assert by_dimension["field"]["status"]["compliance_pct"] == "66.7"
    assert by_dimension["folder"]["WIP"]["files"] == "2"
    assert by_dimension["folder"]["Shared"]["compliance_pct"] == "100.0"
    assert by_dimension["originator"]["ESTM"]["files"] == "2"
    assert by_dimension["originator"]["ENGG"]["compliance_pct"] == "100.0"


def test_compliance_pct_counts_files_not_findings(tmp_path, uk_config):
    """One file with three errors is 0% of one file, not three errors in three files."""
    write(tmp_path, "WIP/bad name.txt")
    write(tmp_path, "WIP/PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01.txt")
    result = check_folder(tmp_path, uk_config)
    assert result.total_files == 2
    assert result.files_with_errors == 1
    assert result.compliance_pct() == 50.0
    assert isinstance(result, CheckResult)


def test_empty_folder_is_fully_compliant(tmp_path, uk_config):
    result = check_folder(tmp_path, uk_config)
    assert result.total_files == 0
    assert result.compliance_pct() == 100.0


def test_container_state_lookup_walks_up_the_tree(tmp_path, uk_config):
    path = tmp_path / "Published" / "Stage3" / "PRJ01-ESTM-ZZ-01-DR-A-0001-A3-C01.pdf"
    assert container_state_for(path, uk_config) == "Published"
    assert container_state_for(tmp_path / "Elsewhere" / "x.pdf", uk_config) is None


def test_helpers(tmp_path, uk_config):
    assert parse_stem("a-b-c", "-") == ["a", "b", "c"]
    parts = parse_stem("PRJ01-ESTM-ZZ-01-DR-A-0001-S0-P01.01", "-")
    assert _facet_key(parts, uk_config, "revision") == "PRJ01-ESTM-ZZ-01-DR-A-0001-S0"
    assert _facet_key(parts, uk_config, "number") == "PRJ01-ESTM-ZZ-01-DR-A-S0-P01.01"
    assert uk_config.id_field_names() == [
        "project",
        "originator",
        "volume_system",
        "level_location",
        "type",
        "role",
        "number",
    ]


def test_suggestions_are_only_offered_when_they_are_clean(minimal_config, tmp_path):
    """The checker never proposes a rename it has not verified to remove every structural error."""
    case_only = write(tmp_path, "WIP/prj1-dr-0001-s0.txt")
    assert check_file(case_only, minimal_config, "WIP")[1] == "PRJ1-DR-0001-S0"

    separator = write(tmp_path, "WIP/PRJ1_DR_0001_S0.txt")
    assert check_file(separator, minimal_config, "WIP")[1] == "PRJ1-DR-0001-S0"

    # digit in an A-Z-only... number must stay digits; upper-casing cannot repair this, so no suggestion
    unfixable = write(tmp_path, "WIP/PRJ1-DR-11x1-S0.txt")
    assert check_file(unfixable, minimal_config, "WIP")[1] is None
