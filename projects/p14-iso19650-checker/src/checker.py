"""Convention-agnostic information container naming checker.

The engine hard-codes no code lists, field lengths, delimiters or folder names: everything comes from
a `ConventionConfig` loaded from YAML (see `conventions/`). Rules implemented:

* structural: field count, field order, length (min/max/exact), charset, regex pattern, code lists
* hygiene: illegal characters, case, empty fields, disallowed extensions, stem/path length
* semantic: status vs CDE container state, duplicate container identifiers, sequential-number gaps,
  revision format (P/C + two integers, optional WIP version suffix) and revision gaps
* metadata: filename vs document title / IFC project name (optional dependencies)
* register: files on disk that are absent from a supplied container register (orphans)

Source of the UK-style codification encoded in `conventions/uk_national_annex.yml`:
CDBB "BIM Toolkit | National Annex Guidance" - https://www.cdbb.cam.ac.uk/files/national_annex_guidance.pdf
(read 2026-10-06; see docs/SOURCES.md). No code list here is written from memory.
"""

from __future__ import annotations

import csv
import fnmatch
import hashlib
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

__all__ = [
    "ConventionConfig",
    "FieldSpec",
    "CheckResult",
    "Issue",
    "load_convention",
    "parse_stem",
    "check_file",
    "check_folder",
    "container_register",
    "compliance_summary",
    "write_csv",
]

ERROR = "error"
WARNING = "warning"


class Provenance(BaseModel):
    """Where a convention came from. Rule 4 of AGENTS.md: provenance is mandatory."""

    name: str
    url: str = ""
    edition: str = ""
    retrieved: str = ""

    @field_validator("retrieved", mode="before")
    @classmethod
    def _stringify_date(cls, value: object) -> str:
        # YAML turns an unquoted 2026-10-06 into a date object; keep provenance as a plain string.
        return value.isoformat() if hasattr(value, "isoformat") else str(value)


class FieldSpec(BaseModel):
    """One facet of the container identifier.

    `charset` is a regex character-class *body* (ranges allowed), e.g. ``A-Z0-9``.
    """

    name: str
    position: int
    length: int | None = None
    min_length: int | None = None
    max_length: int | None = None
    charset: str | None = None
    pattern: str | None = None
    allowed_values: list[str] | None = None
    required: bool = True
    description: str = ""
    source: str = ""

    @model_validator(mode="after")
    def _check_lengths(self) -> FieldSpec:
        if self.length is not None and (self.min_length is not None or self.max_length is not None):
            raise ValueError(f"{self.name}: use either length or min/max_length, not both")
        low = self.length if self.length is not None else self.min_length
        high = self.length if self.length is not None else self.max_length
        if low is not None and high is not None and low > high:
            raise ValueError(f"{self.name}: min_length {low} > max_length {high}")
        return self

    @property
    def low(self) -> int | None:
        return self.length if self.length is not None else self.min_length

    @property
    def high(self) -> int | None:
        return self.length if self.length is not None else self.max_length

    def length_ok(self, value: str) -> bool:
        if self.low is not None and len(value) < self.low:
            return False
        return not (self.high is not None and len(value) > self.high)

    def expected_length(self) -> str:
        if self.length is not None:
            return f"{self.length}"
        if self.min_length is not None and self.max_length is not None:
            return f"{self.min_length}-{self.max_length}"
        if self.min_length is not None:
            return f">={self.min_length}"
        if self.max_length is not None:
            return f"<={self.max_length}"
        return "any"

    def charset_re(self) -> re.Pattern[str] | None:
        if not self.charset:
            return None
        return re.compile(f"^[{self.charset}]+$")

    def pattern_re(self) -> re.Pattern[str] | None:
        if not self.pattern:
            return None
        return re.compile(f"^(?:{self.pattern})$")


class SequenceRules(BaseModel):
    field: str | None = None
    scope: str = "folder"  # folder | global
    warn_on_gap: bool = True


class RevisionRules(BaseModel):
    field: str | None = None
    allow_version_suffix: bool = True
    warn_on_gap: bool = True


class MetadataRules(BaseModel):
    enabled: bool = False
    compare_ifc_project_name: bool = True
    compare_doc_title: bool = True
    ignore_case: bool = True
    required_title_fields: list[str] = Field(default_factory=list)


class ConventionConfig(BaseModel):
    name: str
    description: str = ""
    source: Provenance | None = None
    separator: str = "-"
    case: str = "upper"  # upper | lower | any
    id_fields: list[str] = Field(default_factory=list)
    extension_allowlist: list[str] = Field(default_factory=list)
    illegal_characters: list[str] = Field(default_factory=list)
    path_max_length: int = 260
    max_stem_length: int | None = None
    container_states: dict[str, list[str]] = Field(default_factory=dict)
    fields: list[FieldSpec]
    sequence: SequenceRules = Field(default_factory=SequenceRules)
    revision: RevisionRules = Field(default_factory=RevisionRules)
    metadata: MetadataRules = Field(default_factory=MetadataRules)

    @field_validator("case")
    @classmethod
    def _valid_case(cls, value: str) -> str:
        if value not in {"upper", "lower", "any"}:
            raise ValueError("case must be upper, lower or any")
        return value

    @field_validator("separator")
    @classmethod
    def _valid_separator(cls, value: str) -> str:
        if len(value) != 1:
            raise ValueError("separator must be a single character")
        return value

    @model_validator(mode="after")
    def _check_consistency(self) -> ConventionConfig:
        positions = [f.position for f in self.fields]
        if len(set(positions)) != len(positions):
            raise ValueError("duplicate field positions")
        if sorted(positions) != positions:
            raise ValueError("fields must be listed in position order")
        names = {f.name for f in self.fields}
        for ref in self.id_fields:
            if ref not in names:
                raise ValueError(f"id_fields references unknown field '{ref}'")
        for group, label in ((self.sequence.field, "sequence.field"), (self.revision.field, "revision.field")):
            if group and group not in names:
                raise ValueError(f"{label} references unknown field '{group}'")
        for ref in self.metadata.required_title_fields:
            if ref not in names:
                raise ValueError(f"metadata.required_title_fields references unknown field '{ref}'")
        return self

    def field_by_name(self, name: str) -> FieldSpec | None:
        return next((f for f in self.fields if f.name == name), None)

    def field_by_position(self, position: int) -> FieldSpec | None:
        return next((f for f in self.fields if f.position == position), None)

    def state_for_folder(self, folder_name: str) -> str | None:
        """Container state implied by a folder name, or None if the folder is not a state folder."""
        if folder_name in self.container_states:
            return folder_name
        lowered = folder_name.casefold()
        for state in self.container_states:
            if state.casefold() == lowered:
                return state
        return None

    def id_field_names(self) -> list[str]:
        if self.id_fields:
            return [n for n in self.id_fields if self.field_by_name(n)]
        status = self.field_by_name("status")
        revision = self.field_by_name("revision")
        excluded = {f.name for f in (status, revision) if f}
        return [f.name for f in self.fields if f.name not in excluded]


@dataclass
class Issue:
    path: str
    rule_id: str
    severity: str  # error | warning
    message: str
    suggested_fix: str = ""
    field: str = ""
    container_id: str = ""
    fix_kind: str = ""  # case | separator (trivially fixable by rename)

    @property
    def fixable(self) -> bool:
        return bool(self.fix_kind) and bool(self.suggested_fix)


@dataclass
class CheckResult:
    convention: str = ""
    root: str = ""
    issues: list[Issue] = field(default_factory=list)
    total_files: int = 0
    files_by_state: dict[str, int] = field(default_factory=dict)
    skipped_checks: list[str] = field(default_factory=list)
    renames: list[tuple[str, str]] = field(default_factory=list)  # (old path, new path) if fixable

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == WARNING)

    @property
    def files_with_errors(self) -> int:
        return len({i.path for i in self.issues if i.severity == ERROR})

    def compliance_pct(self) -> float:
        if self.total_files == 0:
            return 100.0
        return round(max(0.0, 100.0 * (1 - self.files_with_errors / self.total_files)), 1)

    def issues_for(self, path: str) -> list[Issue]:
        return [i for i in self.issues if i.path == path]

    def by_rule(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for issue in self.issues:
            counts[issue.rule_id] += 1
        return dict(sorted(counts.items()))

    def to_json(self) -> str:
        return json.dumps(
            {
                "convention": self.convention,
                "root": self.root,
                "total_files": self.total_files,
                "errors": self.error_count,
                "warnings": self.warning_count,
                "compliance_pct": self.compliance_pct(),
                "skipped_checks": self.skipped_checks,
                "issues": [
                    {
                        "path": i.path,
                        "rule_id": i.rule_id,
                        "severity": i.severity,
                        "message": i.message,
                        "field": i.field,
                        "container_id": i.container_id,
                        "suggested_fix": i.suggested_fix,
                        "fix_kind": i.fix_kind,
                    }
                    for i in self.issues
                ],
            },
            indent=2,
        )


def load_convention(path: Path) -> ConventionConfig:
    with open(path, encoding="utf-8") as handle:
        return ConventionConfig(**yaml.safe_load(handle))


def load_convention_text(text: str) -> ConventionConfig:
    return ConventionConfig(**yaml.safe_load(text))


def parse_stem(stem: str, separator: str) -> list[str]:
    return stem.split(separator)


def status_allowed(value: str, allowed: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(value.upper(), pattern.upper()) for pattern in allowed)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def container_state_for(path: Path, config: ConventionConfig) -> str | None:
    """Walk up from the file to the nearest folder named as a container state."""
    for parent in path.parents:
        state = config.state_for_folder(parent.name)
        if state:
            return state
    return None


def _field_issues(stem: str, config: ConventionConfig) -> list[tuple[str, str, str]]:
    """Structural findings for one stem: (rule_id, field name, message). No path/state/extension rules.

    Shared by `check_file` (which turns them into Issues) and by the suggest/apply logic, which only
    offers a rename when re-checking the corrected stem produces no structural errors.
    """
    parts = parse_stem(stem, config.separator)
    findings: list[tuple[str, str, str]] = []

    # A character is "misused as a separator" when using it as one would produce the expected number of
    # fields - that is a naming convention slip. Any other illegal character is just illegal.
    for char in sorted(set(stem) & set(config.illegal_characters)):
        used_as_separator = len(stem.split(char)) == len(config.fields)
        rule = "separator_misuse" if used_as_separator else "illegal_character"
        findings.append((rule, "", f"illegal character {char!r} in file name"))
    for idx, part in enumerate(parts):
        if part == "":
            spec = config.field_by_position(idx)
            findings.append(("empty_field", spec.name if spec else "", f"field {idx + 1} is empty"))
    if len(parts) > len(config.fields):
        findings.append(("field_count", "", f"expected {len(config.fields)} fields, got {len(parts)}"))

    for spec in config.fields:
        if spec.position >= len(parts):
            if spec.required:
                findings.append(("field_missing", spec.name, f"missing field {spec.position + 1} ({spec.name})"))
            continue
        value = parts[spec.position]
        if not spec.length_ok(value):
            findings.append(
                (
                    "field_length",
                    spec.name,
                    f"{spec.name}: expected length {spec.expected_length()}, got {len(value)} ('{value}')",
                )
            )
        charset_re = spec.charset_re()
        if charset_re and not charset_re.match(value):
            findings.append(
                ("field_charset", spec.name, f"{spec.name}: '{value}' contains characters outside {spec.charset}")
            )
        pattern_re = spec.pattern_re()
        if pattern_re and not pattern_re.match(value):
            findings.append(("field_pattern", spec.name, f"{spec.name}: '{value}' does not match {spec.pattern}"))
        if spec.allowed_values and value not in spec.allowed_values:
            findings.append(
                (
                    "field_allowed_values",
                    spec.name,
                    f"{spec.name}: '{value}' is not an allowed value ({', '.join(spec.allowed_values)})",
                )
            )
        if config.case == "upper" and value != value.upper():
            findings.append(("field_case", spec.name, f"{spec.name}: '{value}' should be upper case"))
        elif config.case == "lower" and value != value.lower():
            findings.append(("field_case", spec.name, f"{spec.name}: '{value}' should be lower case"))
    return findings


def _candidate_stems(stem: str, config: ConventionConfig) -> list[tuple[str, str]]:
    """Trivially correctable stems, most obvious first: case fix, then separator fix."""
    candidates: list[tuple[str, str]] = []
    parts = parse_stem(stem, config.separator)
    if len(parts) == len(config.fields):
        fixed = [v.upper() for v in parts] if config.case == "upper" else list(parts)
        if config.case == "lower":
            fixed = [v.lower() for v in parts]
        candidates.append((config.separator.join(fixed), "case"))
    for alternative in config.illegal_characters:
        split = stem.split(alternative)
        if len(split) == len(config.fields):
            fixed_split = (
                [v.upper() for v in split]
                if config.case == "upper"
                else [v.lower() for v in split]
                if config.case == "lower"
                else list(split)
            )
            candidates.append((config.separator.join(fixed_split), "separator"))
    return [(s, kind) for s, kind in candidates if s != stem]


def _suggest_stem(stem: str, config: ConventionConfig) -> tuple[str | None, str]:
    """A corrected stem only when re-checking it clears *every* structural error.

    This is the guard behind `--suggest`/`--apply`: the checker never proposes a rename it has not
    verified to be clean, so an applied rename cannot introduce a new violation.
    """
    if not _field_issues(stem, config):
        return None, ""
    for candidate, kind in _candidate_stems(stem, config):
        if not _field_issues(candidate, config):
            return candidate, kind
    return None, ""


def check_file(
    path: Path,
    config: ConventionConfig,
    container_state: str | None = None,
    display_path: str | None = None,
) -> tuple[list[Issue], str | None]:
    """Check one file. Returns (issues, suggested_stem or None)."""
    shown = display_path or str(path)
    stem = path.stem
    issues: list[Issue] = []
    parts = parse_stem(stem, config.separator)
    container_id = config.separator.join(parts[: len(config.id_field_names())])

    for rule_id, field_name, message in _field_issues(stem, config):
        fix, kind = "", ""
        if rule_id == "field_case" and field_name:
            spec = config.field_by_name(field_name)
            if spec and spec.position < len(parts):
                value = parts[spec.position]
                fix = value.upper() if config.case == "upper" else value.lower()
                kind = "case"
        severity = WARNING if rule_id == "field_case" else ERROR
        issues.append(Issue(shown, rule_id, severity, message, fix, field_name, container_id, kind))

    # --- status vs container state --------------------------------------------------------
    status_spec = config.field_by_name("status")
    if status_spec and status_spec.position < len(parts) and container_state:
        allowed = config.container_states.get(container_state, [])
        if allowed and not status_allowed(parts[status_spec.position], allowed):
            issues.append(
                Issue(
                    shown,
                    "status_container_mismatch",
                    ERROR,
                    f"status '{parts[status_spec.position]}' is not valid in the {container_state} state "
                    f"(expected one of {', '.join(allowed)})",
                    field=status_spec.name,
                    container_id=container_id,
                )
            )

    # --- extension and path hygiene -------------------------------------------------------
    ext = path.suffix.lower()
    if config.extension_allowlist and ext not in config.extension_allowlist:
        allowed = ", ".join(config.extension_allowlist)
        issues.append(Issue(shown, "disallowed_extension", ERROR, f"extension '{ext}' is not allowed ({allowed})"))
    if config.max_stem_length and len(stem) > config.max_stem_length:
        issues.append(
            Issue(
                shown,
                "stem_length",
                WARNING,
                f"file name stem is {len(stem)} characters (max {config.max_stem_length})",
            )
        )
    if len(shown) > config.path_max_length:
        issues.append(
            Issue(shown, "path_length", WARNING, f"path length {len(shown)} exceeds {config.path_max_length}")
        )

    suggested, _kind = _suggest_stem(stem, config)
    return issues, suggested


def _identifier_key(parts: list[str], config: ConventionConfig) -> str:
    names = config.id_field_names()
    values: list[str] = []
    for name in names:
        spec = config.field_by_name(name)
        value = parts[spec.position] if spec and spec.position < len(parts) else ""
        values.append(value)
    return config.separator.join(values)


def _facet_key(parts: list[str], config: ConventionConfig, drop_field: str | None) -> str:
    """Series key: the identifier facets plus the metadata facets, minus one facet.

    Built from field *names*, not positions, so a convention that inserts an extra non-identifier
    facet (e.g. an asset classification) does not split one series into several and invent gaps.
    """
    names = [n for n in config.id_field_names() if n != drop_field]
    for extra in ("status", "revision"):
        spec = config.field_by_name(extra)
        if extra == drop_field or spec is None or not spec.required or extra in names:
            continue
        names.append(extra)
    values: list[str] = []
    for name in names:
        spec = config.field_by_name(name)
        if spec and spec.position < len(parts):
            values.append(parts[spec.position])
    return config.separator.join(values)


def check_folder(
    folder: Path,
    config: ConventionConfig,
    register: Path | None = None,
    display_root: str | None = None,
) -> CheckResult:
    """Check every file under `folder`. Optionally flag orphans against an existing register."""
    result = CheckResult(convention=config.name, root=display_root or str(folder))
    seen: dict[str, str] = {}
    series: dict[str, set[int]] = defaultdict(set)
    revisions: dict[str, set[tuple[str, int]]] = defaultdict(set)
    meta_checker = None
    if config.metadata.enabled:
        from metadata import MetadataReader  # local import: optional dependency guard

        meta_checker = MetadataReader(config.metadata)

    number_spec = config.field_by_name(config.sequence.field) if config.sequence.field else None
    revision_spec = config.field_by_name(config.revision.field) if config.revision.field else None

    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        shown = str(path.relative_to(folder)).replace("\\", "/")
        state = container_state_for(path, config)
        result.total_files += 1
        if state:
            result.files_by_state[state] = result.files_by_state.get(state, 0) + 1

        issues, suggested = check_file(path, config, state, shown)
        parts = parse_stem(path.stem, config.separator)

        # duplicate container identifiers. Two qualifications, both from ISO 19650 practice:
        #   * uniqueness is container id *plus revision* - the identifier is stable across revisions,
        #     so two files differing only by revision are a revision history, not a duplicate (that is
        #     what the revision-gap rule is for);
        #   * uniqueness is per CDE *state* - one container legitimately appears in WIP, Shared,
        #     Published and Archive over its life, so the same id in two states is the container
        #     lifecycle, not a collision.
        key = _identifier_key(parts, config)
        if key.strip(config.separator):
            revision_spec = config.field_by_name(config.revision.field) if config.revision.field else None
            revision_value = (
                parts[revision_spec.position] if revision_spec and revision_spec.position < len(parts) else ""
            )
            unique_key = f"{state or '-'}|{key}|{revision_value}"
            if unique_key in seen:
                issues.append(
                    Issue(
                        shown,
                        "duplicate_identifier",
                        ERROR,
                        f"container id '{key}'"
                        + (f" revision '{revision_value}'" if revision_value else "")
                        + (f" already exists in the {state} state" if state else "")
                        + f"; first seen at {seen[unique_key]}",
                        container_id=key,
                    )
                )
            else:
                seen[unique_key] = shown

        # sequential number gaps within a series
        if number_spec and number_spec.position < len(parts):
            raw = parts[number_spec.position]
            if raw.isdigit():
                base_key = _facet_key(parts, config, config.sequence.field) if config.sequence.scope == "folder" else ""
                folder_key = str(Path(shown).parent).replace("\\", "/")
                series_key = f"{folder_key}|{base_key}" if config.sequence.scope == "folder" else base_key
                series[series_key].add(int(raw))

        # revision format + gaps
        if revision_spec and revision_spec.position < len(parts):
            rev = parts[revision_spec.position]
            parsed = _parse_revision(rev, config)
            if parsed is None:
                issues.append(
                    Issue(
                        shown,
                        "revision_format",
                        ERROR,
                        f"revision '{rev}' is not <P|C><nn>[.<nn>] (Annex 2.1.1)",
                        field=revision_spec.name,
                        container_id=key,
                    )
                )
            else:
                kind, number, version = parsed
                revisions[_facet_key(parts, config, config.revision.field)].add((kind, number))

        if meta_checker is not None and not _field_issues(path.stem, config):
            # Only draw metadata conclusions from a name that parses cleanly: a file already flagged for
            # a structural fault must not also be accused of a title mismatch caused by that fault.
            issues.extend(meta_checker.check(path, parts, config, shown, key))

        if suggested:
            new_shown = str(Path(shown).with_name(suggested + path.suffix)).replace("\\", "/")
            result.renames.append((shown, new_shown))
        result.issues.extend(issues)

    if number_spec and config.sequence.warn_on_gap:
        width = number_spec.low or 4
        for series_key, numbers in series.items():
            _add_gaps(result, numbers, "number_gap", number_spec.name, "number", series_key, width)
    if revision_spec and config.revision.warn_on_gap:
        for series_key, pairs in revisions.items():
            for kind in {k for k, _ in pairs}:
                numbers = {n for k, n in pairs if k == kind}
                _add_gaps(result, numbers, "revision_gap", revision_spec.name, f"{kind} revision", series_key, 2)

    if register:
        result.issues.extend(_orphan_issues(folder, register, result))
    if meta_checker is not None:
        # Skipped checks are only known once the walk is over (an optional backend may be missing).
        result.skipped_checks.extend(meta_checker.skipped())
    return result


def _parse_revision(value: str, config: ConventionConfig) -> tuple[str, int, int | None] | None:
    """`P01`, `C02`, `P01.01` -> ('P', 1, 1). Annex 2.1.1: two integers, P or C prefix."""
    match = re.fullmatch(r"([PC])(\d{2})(?:\.(\d{2}))?", value)
    if not match:
        return None
    if "." in value and not config.revision.allow_version_suffix:
        return None
    return match.group(1), int(match.group(2)), int(match.group(3)) if match.group(3) else None


def _add_gaps(
    result: CheckResult,
    numbers: set[int],
    rule_id: str,
    field_name: str,
    label: str,
    series_key: str,
    width: int,
) -> None:
    if len(numbers) < 2:
        return
    missing = sorted(set(range(min(numbers), max(numbers) + 1)) - numbers)
    for value in missing:
        result.issues.append(
            Issue(
                path="(series)",
                rule_id=rule_id,
                severity=WARNING,
                message=(f"{label} gap in series '{series_key}': {field_name} {value:0{width}d} is missing"),
                field=field_name,
                container_id=series_key,
            )
        )


def _orphan_issues(folder: Path, register: Path, result: CheckResult) -> list[Issue]:
    """Files on disk that are not in the supplied container register (spec: orphan files)."""
    if not register.exists():
        return [Issue(str(register), "register_missing", WARNING, f"container register '{register}' does not exist")]
    known: set[str] = set()
    with open(register, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            value = row.get("path") or row.get("relative_path") or ""
            known.add(value.strip().replace("\\", "/"))
    issues: list[Issue] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        shown = str(path.relative_to(folder)).replace("\\", "/")
        if shown not in known:
            issues.append(
                Issue(shown, "orphan_file", ERROR, f"file is not listed in the container register ({register.name})")
            )
    return issues


def container_register(folder: Path, config: ConventionConfig) -> list[dict[str, str]]:
    """Container register rows: one per file, with parsed facets, state and content hash."""
    rows: list[dict[str, str]] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        shown = str(path.relative_to(folder)).replace("\\", "/")
        parts = parse_stem(path.stem, config.separator)
        row: dict[str, str] = {
            "path": shown,
            "container_id": config.separator.join(parts[: len(config.id_field_names())]),
            "extension": path.suffix.lower(),
            "size_bytes": str(path.stat().st_size),
            "sha256": _sha256(path),
            "state": container_state_for(path, config) or "",
        }
        for spec in config.fields:
            row[spec.name] = parts[spec.position] if spec.position < len(parts) else ""
        rows.append(row)
    return rows


def compliance_summary(folder: Path, config: ConventionConfig, result: CheckResult) -> list[dict[str, str]]:
    """Compliance % overall, by field, by folder (state) and by originator (spec requirement)."""
    rows: list[dict[str, str]] = []
    total = max(result.total_files, 1)
    rows.append(
        {
            "dimension": "overall",
            "key": "all",
            "files": str(result.total_files),
            "errors": str(result.error_count),
            "warnings": str(result.warning_count),
            "compliance_pct": f"{result.compliance_pct():.1f}",
        }
    )

    def pct(files_with_error: int, files: int) -> str:
        return f"{max(0.0, 100.0 * (1 - files_with_error / max(files, 1))):.1f}"

    # by field
    files_with_field_issue = {spec.name: set() for spec in config.fields}
    counts = {spec.name: 0 for spec in config.fields}
    for issue in result.issues:
        if issue.field in counts and issue.path != "(series)":
            counts[issue.field] += 1
            files_with_field_issue[issue.field].add(issue.path)
    for spec in config.fields:
        rows.append(
            {
                "dimension": "field",
                "key": spec.name,
                "files": str(total),
                "errors": str(counts[spec.name]),
                "warnings": "",
                "compliance_pct": pct(len(files_with_field_issue[spec.name]), total),
            }
        )

    # by folder / container state
    state_errors: dict[str, set[str]] = defaultdict(set)
    state_warnings: dict[str, int] = defaultdict(int)
    for issue in result.issues:
        if issue.path == "(series)":
            continue
        for parent in Path(issue.path).parents:
            state = config.state_for_folder(parent.name)
            if state:
                if issue.severity == ERROR:
                    state_errors[state].add(issue.path)
                else:
                    state_warnings[state] += 1
                break
    for state, files in sorted(result.files_by_state.items()):
        rows.append(
            {
                "dimension": "folder",
                "key": state,
                "files": str(files),
                "errors": str(len(state_errors.get(state, set()))),
                "warnings": str(state_warnings.get(state, 0)),
                "compliance_pct": pct(len(state_errors.get(state, set())), files),
            }
        )

    # by originator
    spec_originator = config.field_by_name("originator")
    by_originator: dict[str, list[Path]] = defaultdict(list)
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        shown = str(path.relative_to(folder)).replace("\\", "/")
        parts = parse_stem(path.stem, config.separator)
        if spec_originator and spec_originator.position < len(parts):
            by_originator[parts[spec_originator.position]].append(Path(shown))
    origin_errors: dict[str, set[str]] = defaultdict(set)
    origin_warnings: dict[str, int] = defaultdict(int)
    for issue in result.issues:
        if issue.path == "(series)":
            continue
        parts = parse_stem(Path(issue.path).stem, config.separator)
        if spec_originator and spec_originator.position < len(parts):
            key = parts[spec_originator.position]
            if issue.severity == ERROR:
                origin_errors[key].add(issue.path)
            else:
                origin_warnings[key] += 1
    for originator, paths in sorted(by_originator.items()):
        shown_set = {str(p).replace("\\", "/") for p in paths}
        rows.append(
            {
                "dimension": "originator",
                "key": originator,
                "files": str(len(shown_set)),
                "errors": str(len(origin_errors.get(originator, set()))),
                "warnings": str(origin_warnings.get(originator, 0)),
                "compliance_pct": pct(len(origin_errors.get(originator, set())), len(shown_set)),
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str] | None = None) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    columns = fieldnames or list(rows[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
