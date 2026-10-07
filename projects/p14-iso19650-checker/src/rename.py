"""`--apply` renames and their rollback.

Design rules (spec): `--apply` never guesses. A file is renamed only when *every* error found on it is
trivially fixable by the checker's suggest mode (case and separator problems). Each rename is written
to `rename_log.csv` with the pre-rename sha256 so `rollback` can verify it is restoring the same
content, and it is reversible by construction.
"""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

LOG_FIELDS = ["timestamp", "old_path", "new_path", "status", "detail", "sha256_before"]


@dataclass
class RenameRecord:
    old_path: str
    new_path: str
    status: str  # renamed | skipped | failed
    detail: str = ""
    sha256_before: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"))

    def as_row(self) -> dict[str, str]:
        return {
            "timestamp": self.timestamp,
            "old_path": self.old_path,
            "new_path": self.new_path,
            "status": self.status,
            "detail": self.detail,
            "sha256_before": self.sha256_before,
        }


@dataclass
class ApplyResult:
    records: list[RenameRecord] = field(default_factory=list)
    dry_run: bool = True
    log_path: Path | None = None

    @property
    def renamed(self) -> int:
        return sum(1 for r in self.records if r.status == "renamed")

    @property
    def skipped(self) -> int:
        return sum(1 for r in self.records if r.status == "skipped")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_log(log_path: Path, records: list[RenameRecord]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=LOG_FIELDS)
        writer.writeheader()
        writer.writerows(r.as_row() for r in records)


def read_log(log_path: Path) -> list[RenameRecord]:
    with open(log_path, newline="", encoding="utf-8") as handle:
        return [
            RenameRecord(
                old_path=row["old_path"],
                new_path=row["new_path"],
                status=row["status"],
                detail=row.get("detail", ""),
                sha256_before=row.get("sha256_before", ""),
                timestamp=row.get("timestamp", ""),
            )
            for row in csv.DictReader(handle)
        ]


def _same_file(a: Path, b: Path) -> bool:
    """True when both paths point at the same file, including a case-only difference (Windows)."""
    try:
        return a.samefile(b)
    except OSError:
        return False


def apply_renames(
    folder: Path,
    renames: list[tuple[str, str]],
    dry_run: bool = True,
    log_path: Path | None = None,
) -> ApplyResult:
    """Rename files inside `folder`. `renames` are (relative old path, relative new path) pairs.

    Dry-run by default: nothing is touched, the log is still written so the plan can be reviewed.
    """
    records: list[RenameRecord] = []
    for old_rel, new_rel in sorted(renames):
        source = folder / old_rel
        target = folder / new_rel
        if not source.exists():
            records.append(RenameRecord(old_rel, new_rel, "skipped", "source no longer exists"))
            continue
        if target.exists() and not _same_file(source, target):
            records.append(RenameRecord(old_rel, new_rel, "skipped", "target already exists"))
            continue
        digest = sha256(source)
        if dry_run:
            records.append(RenameRecord(old_rel, new_rel, "renamed", "dry-run", digest))
            continue
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
        except OSError as exc:  # pragma: no cover - filesystem specific
            records.append(RenameRecord(old_rel, new_rel, "failed", str(exc), digest))
        else:
            records.append(RenameRecord(old_rel, new_rel, "renamed", "", digest))
    result = ApplyResult(records=records, dry_run=dry_run, log_path=log_path)
    if log_path is not None:
        write_log(log_path, records)
    return result


def rollback(folder: Path, log_path: Path) -> ApplyResult:
    """Undo renames recorded in `log_path`, newest first, verifying content hash."""
    records = read_log(log_path)
    undone: list[RenameRecord] = []
    for record in reversed(records):
        if record.status != "renamed":
            undone.append(RenameRecord(record.old_path, record.new_path, "skipped", "not renamed"))
            continue
        if record.detail == "dry-run":
            # A dry-run row records what *would* have happened; nothing moved, so there is nothing to undo.
            undone.append(RenameRecord(record.old_path, record.new_path, "skipped", "dry run, nothing was renamed"))
            continue
        current = folder / record.new_path
        original = folder / record.old_path
        if not current.exists():
            undone.append(RenameRecord(record.new_path, record.old_path, "skipped", "renamed file missing"))
            continue
        # On a case-insensitive filesystem a case-only rename leaves both paths "existing" and pointing
        # at the same file, so identity has to be compared, not the mere existence of the target name.
        if original.exists() and not _same_file(current, original):
            undone.append(RenameRecord(record.new_path, record.old_path, "skipped", "original path occupied"))
            continue
        if record.sha256_before and sha256(current) != record.sha256_before:
            undone.append(RenameRecord(record.new_path, record.old_path, "skipped", "content changed since rename"))
            continue
        try:
            current.rename(original)
        except OSError as exc:  # pragma: no cover - filesystem specific
            undone.append(RenameRecord(record.new_path, record.old_path, "failed", str(exc)))
        else:
            undone.append(RenameRecord(record.new_path, record.old_path, "renamed", "rolled back"))
    return ApplyResult(records=undone, dry_run=False, log_path=log_path)
