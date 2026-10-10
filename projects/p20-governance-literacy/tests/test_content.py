"""Content completeness: the site itself, the workshop pack, RACI and standards.

These are the tests that fail when someone deletes a page or quietly softens a
claim. They are deliberately blunt.
"""

from __future__ import annotations

from pathlib import Path

import checks
import config
import yaml

DOCS = checks.PROJECT_DIR / "docs"


def read(rel: str) -> str:
    return (DOCS / rel).read_text(encoding="utf-8")


# ------------------------------------------------------------------ the site
def test_nav_covers_every_page() -> None:
    nav_text = (checks.PROJECT_DIR / "mkdocs.yml").read_text(encoding="utf-8")
    on_disk = {p.relative_to(DOCS).as_posix() for p in DOCS.rglob("*.md")}
    listed = {line.split(": ", 1)[1].strip() for line in nav_text.splitlines() if ".md" in line and ": " in line}
    assert on_disk == listed, f"nav mismatch: only on disk {on_disk - listed}, only in nav {listed - on_disk}"


def test_spec_content_items_all_exist() -> None:
    """Each of the twelve content items in the spec has a real page."""
    required = [
        "governance/framework.md",
        "governance/roles.md",
        "generated/raci.md",
        "generated/data-dictionary.md",
        "generated/glossary.md",
        "generated/metric-registry.md",
        "data/classification.md",
        "data/quality-policy.md",
        "data/naming-standards.md",
        "generated/standards-register.md",
        "standards/handover.md",
        "process/data-request.md",
        "dashboards/index.md",
        "training/workshop.md",
        "runbooks.md",
        "adr-index.md",
    ]
    missing = [rel for rel in required if not (DOCS / rel).is_file()]
    assert missing == []


def test_dashboard_guide_covers_every_dashboard() -> None:
    index = read("dashboards/index.md")
    for page in (
        "p06-space-utilisation.md",
        "p07-assets-and-maintenance.md",
        "p08-energy-and-carbon.md",
        "p09-compliance.md",
        "p10-institutional-return.md",
        "data-quality-scorecard.md",
    ):
        assert page in index, f"{page} is not linked from the dashboard guide"
        text = read(f"dashboards/{page}")
        for heading in ("Question it answers", "Common misreadings", "Who to ask"):
            assert heading in text, f"{page} is missing '{heading}'"


def test_dashboard_pages_state_synthetic_data() -> None:
    index = read("dashboards/index.md")
    assert "synthetic" in index.lower()


# ------------------------------------------------------------ training pack
def test_workshop_pack_is_deliverable_from_the_folder_alone() -> None:
    """Everything a facilitator needs, in this folder, in one place."""
    workshop = read("training/workshop.md")
    assert "Learning outcomes" in workshop
    assert "45 minutes" in workshop
    assert "Materials checklist" in workshop
    for exercise in ("Exercise 1", "Exercise 2", "Exercise 3"):
        assert exercise in workshop
        assert exercise in read("training/exercises.md")
    assert "Answer key" in workshop or "answer key" in workshop
    for page in (
        "training/quiz.md",
        "training/answer-key.md",
        "training/feedback-form.md",
        "training/slide-outline.md",
        "training/facilitator-notes.md",
        "training/ten-minute-demo.md",
    ):
        assert (DOCS / page).is_file()


def test_quiz_has_ten_questions_and_key_has_twelve_rows() -> None:
    quiz = read("training/quiz.md")
    numbered = [line for line in quiz.splitlines() if line.strip()[:2].rstrip(".").isdigit() and ". " in line]
    assert len(numbered) == 12, numbered
    key = read("training/answer-key.md")
    rows = [line for line in key.splitlines() if line.startswith("| ") and line.strip().endswith("|")]
    assert len(rows) >= 13, "answer key needs a row per question"


def test_facilitator_notes_cover_the_three_habit_questions() -> None:
    notes = read("training/facilitator-notes.md")
    for question in ("Is this number right?", "Can I use this for a real decision?", "Who do I complain to?"):
        assert question in notes


def test_slide_outline_leaves_slides_to_the_human() -> None:
    outline = read("training/slide-outline.md")
    assert "Outline only" in outline
    assert "built by the human" in outline


# -------------------------------------------------------------- governance
def test_raci_has_every_domain_with_one_accountable_role() -> None:
    raci = yaml.safe_load((checks.PROJECT_DIR / "raci.yml").read_text(encoding="utf-8"))
    domains = {d["id"] for d in raci["domains"]}
    assert domains == {"space", "assets", "energy_carbon", "compliance", "bim"}
    for domain in raci["domains"]:
        assert domain["activities"], domain["id"]
        for activity in domain["activities"]:
            letters = [activity[role] for role in ("owner", "steward", "custodian", "consumer")]
            assert set(letters) <= {"R", "A", "C", "I"}, activity
            assert letters.count("A") == 1, f"exactly one accountable role: {activity}"
        assert domain["decision_rights"] and domain["escalation"], domain["id"]
    assert len(raci["roles"]) == 4
    assert raci["decision_rights_global"]


def test_framework_states_the_four_roles_and_decision_rights() -> None:
    text = read("governance/framework.md")
    for word in ("Owner", "Steward", "Custodian", "Consumer"):
        assert word in text
    assert "Escalation path" in text
    assert "Decision rights" in text


def test_standards_register_statuses_are_honest() -> None:
    standards = yaml.safe_load((checks.PROJECT_DIR / "standards.yml").read_text(encoding="utf-8"))
    valid = set(standards["statuses"])
    entries = {s["id"]: s for s in standards["standards"]}
    assert {"iso_19650", "uniclass", "cobie", "ghg_protocol", "sfG20", "hesa_emr", "trac"} <= set(entries)
    for entry in standards["standards"]:
        assert entry["status"] in valid
        assert entry["limitations"].strip(), entry["id"]
        assert entry["url"].startswith("http"), entry["id"]
    # The claims this pack must not overstate.
    assert entries["uniclass"]["status"] == "mock"
    assert entries["hesa_emr"]["status"] == "mock"
    assert entries["sfG20"]["status"] == "not-obtained"
    assert entries["trac"]["status"] == "awareness-only"
    assert entries["ghg_protocol"]["status"] == "awareness-only"


def test_classification_page_is_honest_about_legal_advice() -> None:
    text = read("data/classification.md")
    assert "not legal advice" in text.lower()
    for level in ("Public", "Internal", "Confidential"):
        assert level in text
    for case in ("Work orders", "Occupancy sensors", "Inspection"):
        assert case in text


def test_quality_policy_points_at_p03_dimensions_and_response_times() -> None:
    text = read("data/quality-policy.md")
    for dimension in (
        "completeness",
        "uniqueness",
        "validity",
        "consistency",
        "timeliness",
        "referential integrity",
        "reconciliation",
    ):
        assert dimension in text
    assert "error" in text and "24 hours" in text
    assert "docs/dq-policy.md" in text


def test_naming_standards_cover_layers_ids_units_and_time() -> None:
    text = read("data/naming-standards.md")
    for token in ("stg_", "dim_", "fct_", "mart_", "_ts_utc", "_date", "nia_m2", "kgco2e", "B007", "ifc:", "UTC"):
        assert token in text, token


def test_handover_guide_links_the_checks_and_lists_roles() -> None:
    text = read("standards/handover.md")
    assert "Owner" in text and "Custodian" in text and "Steward" in text
    assert "AIR" in text
    assert "COBie" in text or "classification" in text


def test_data_request_process_has_intake_triage_and_sla() -> None:
    text = read("process/data-request.md")
    assert "Intake form" in text
    assert "Triage criteria" in text
    assert "Service levels" in text
    assert "classification" in text.lower()


def test_metric_change_log_has_entries() -> None:
    text = read("process/metric-change-log.md")
    rows = [line for line in text.splitlines() if line.startswith("| 2026-")]
    assert len(rows) >= 3, "the change log needs real entries, not headings"


def test_runbooks_cover_the_common_failures() -> None:
    text = read("runbooks.md")
    for tag in ("RB1", "RB2", "RB3", "RB4", "RB5", "RB6", "RB7", "RB8"):
        assert tag in text
    assert "personal" in text.lower()


def test_adr_index_points_at_the_repository_records() -> None:
    text = read("adr-index.md")
    assert "001-python-packaging.md" in text
    assert "002-orchestrator-choice.md" in text


def test_reference_index_points_at_every_project() -> None:
    text = read("reference-index.md")
    for project in sorted(p.name for p in (config.REPO_ROOT / "projects").iterdir() if p.is_dir()):
        assert project in text, f"{project} is missing from the reference index"


# --------------------------------------------------------------- synthetic
def test_every_page_carries_the_synthetic_statement() -> None:
    offenders = []
    for path in sorted(DOCS.rglob("*.md")):
        text = path.read_text(encoding="utf-8").lower()
        if path.parts[-2] == "generated":
            continue  # generated pages carry the standard note from the renderer
        if "synthetic" not in text:
            offenders.append(path.relative_to(DOCS).as_posix())
    assert offenders == [], offenders


def test_generated_pages_carry_the_banner_and_note() -> None:
    for rel in config.GENERATED_PAGES:
        text = (DOCS / rel).read_text(encoding="utf-8")
        assert text.startswith("<!-- GENERATED FILE"), rel
        assert "synthetic" in text.lower(), rel


def test_registry_yaml_files_are_the_source_of_truth() -> None:
    for name in ("metrics.yml", "glossary.yml", "raci.yml", "standards.yml"):
        path = checks.PROJECT_DIR / name
        assert path.is_file(), name
        assert yaml.safe_load(path.read_text(encoding="utf-8")) is not None


def test_dbt_models_dir_is_referenced_by_the_dictionary() -> None:
    meta_text = read("generated/data-dictionary.md")
    assert "platform/dbt/models" in meta_text
    assert "mart_space_utilisation" in meta_text


def test_dq_scores_page_is_honest_about_missing_runs(tmp_path: Path) -> None:
    import checks as gate_mod

    pages = gate_mod.render_pages(dq_scores_csv=tmp_path / "absent.csv")
    assert "No data quality results in this checkout" in pages["generated/dq-scores.md"]
