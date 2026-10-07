"""`--apply` and rollback: the spec's acceptance criterion is that a rename is reversible."""

from __future__ import annotations

from pathlib import Path

from conftest import write
from rename import apply_renames, read_log, rollback, write_log


def sidecar(root: Path) -> Path:
    """A log path outside the tree under test: a log kept inside it would be an extra file."""
    outside = root.parent / f"{root.name}_logs"
    outside.mkdir(exist_ok=True)
    return outside / "rename_log.csv"


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_dry_run_changes_nothing_but_writes_the_plan(tmp_path):
    lower = write(tmp_path, "WIP/prj1-dr-0001-s0.txt")
    before = snapshot(tmp_path)
    log = sidecar(tmp_path)

    result = apply_renames(
        tmp_path, [("WIP/prj1-dr-0001-s0.txt", "WIP/PRJ1-DR-0001-S0.txt")], dry_run=True, log_path=log
    )

    assert result.renamed == 1
    assert result.dry_run is True
    assert lower.exists()
    assert snapshot(tmp_path) == before
    rows = read_log(log)
    assert [r.status for r in rows] == ["renamed"]
    assert rows[0].detail == "dry-run"
    assert len(rows[0].sha256_before) == 64


def test_apply_then_rollback_restores_the_tree_exactly(tmp_path):
    lower = write(tmp_path, "WIP/prj1-dr-0001-s0.txt", "content one\n")
    underscored = write(tmp_path, "WIP/prj1_dr_0001_s1.txt", "content two\n")
    before = snapshot(tmp_path)
    log = sidecar(tmp_path)
    renames = [
        ("WIP/prj1-dr-0001-s0.txt", "WIP/PRJ1-DR-0001-S0.txt"),
        ("WIP/prj1_dr_0001_s1.txt", "WIP/PRJ1-DR-0001-S1.txt"),
    ]

    applied = apply_renames(tmp_path, renames, dry_run=False, log_path=log)
    assert applied.renamed == 2
    # Directory listing rather than exists(): a case-insensitive filesystem resolves both spellings.
    assert {p.name for p in (tmp_path / "WIP").iterdir()} == {"PRJ1-DR-0001-S0.txt", "PRJ1-DR-0001-S1.txt"}
    assert (tmp_path / "WIP" / "PRJ1-DR-0001-S0.txt").read_text() == "content one\n"

    undone = rollback(tmp_path, log)
    assert undone.renamed == 2
    assert snapshot(tmp_path) == before
    assert lower.exists() and underscored.exists()


def test_rollback_handles_case_only_renames(tmp_path):
    """On a case-insensitive filesystem both names 'exist' while only one file does."""
    lower = write(tmp_path, "WIP/prj1-dr-0001-s0.txt")
    log = sidecar(tmp_path)
    apply_renames(tmp_path, [("WIP/prj1-dr-0001-s0.txt", "WIP/PRJ1-DR-0001-S0.txt")], dry_run=False, log_path=log)

    outcome = rollback(tmp_path, log)
    assert outcome.renamed == 1
    # Directory listing, not exists(): on Windows both spellings resolve to the same file.
    assert {p.name for p in (tmp_path / "WIP").iterdir()} == {"prj1-dr-0001-s0.txt"}
    assert lower.exists()


def test_rollback_refuses_content_that_changed_since_the_rename(tmp_path):
    write(tmp_path, "WIP/prj1-dr-0001-s0.txt", "original\n")
    log = sidecar(tmp_path)
    apply_renames(tmp_path, [("WIP/prj1-dr-0001-s0.txt", "WIP/PRJ1-DR-0001-S0.txt")], dry_run=False, log_path=log)
    (tmp_path / "WIP" / "PRJ1-DR-0001-S0.txt").write_text("edited after the rename\n", encoding="utf-8")

    outcome = rollback(tmp_path, log)
    assert outcome.renamed == 0
    assert outcome.records[0].detail == "content changed since rename"


def test_apply_skips_when_the_target_is_occupied_by_a_different_file(tmp_path):
    """Not a case-only rename: a genuinely different file already occupies the target name."""
    write(tmp_path, "WIP/prj1-dr-0001-s0.txt")
    write(tmp_path, "WIP/OTHER-NAME.txt", "a different file that already lives there\n")
    log = sidecar(tmp_path)

    outcome = apply_renames(tmp_path, [("WIP/prj1-dr-0001-s0.txt", "WIP/OTHER-NAME.txt")], dry_run=False, log_path=log)
    assert outcome.renamed == 0
    assert outcome.records[0].detail == "target already exists"


def test_apply_skips_a_missing_source(tmp_path):
    log = sidecar(tmp_path)
    outcome = apply_renames(tmp_path, [("WIP/gone.txt", "WIP/PRJ1-DR-0001-S0.txt")], dry_run=False, log_path=log)
    assert outcome.skipped == 1
    assert outcome.records[0].detail == "source no longer exists"


def test_rollback_is_a_no_op_on_a_dry_run_log(tmp_path):
    write(tmp_path, "WIP/prj1-dr-0001-s0.txt")
    log = sidecar(tmp_path)
    apply_renames(tmp_path, [("WIP/prj1-dr-0001-s0.txt", "WIP/PRJ1-DR-0001-S0.txt")], dry_run=True, log_path=log)

    outcome = rollback(tmp_path, log)
    assert outcome.renamed == 0
    assert outcome.records[0].detail == "dry run, nothing was renamed"
    assert (tmp_path / "WIP" / "prj1-dr-0001-s0.txt").exists()


def test_log_round_trip(tmp_path):
    write(tmp_path, "WIP/prj1-dr-0001-s0.txt")
    log = sidecar(tmp_path)
    apply_renames(tmp_path, [("WIP/prj1-dr-0001-s0.txt", "WIP/PRJ1-DR-0001-S0.txt")], dry_run=False, log_path=log)
    rows = read_log(log)
    assert rows[0].old_path == "WIP/prj1-dr-0001-s0.txt"
    assert rows[0].new_path == "WIP/PRJ1-DR-0001-S0.txt"
    assert rows[0].timestamp  # recorded, so an audit trail exists

    # a hand-written log is honoured too (that is the point of writing it out)
    write_log(log, [])
    assert read_log(log) == []
