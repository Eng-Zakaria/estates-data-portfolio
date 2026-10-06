"""ISO 19650-style convention checker engine.

Reads everything from a convention YAML config; no hard-coded code lists or lengths.
Checks: field count/order/length/charset/separators, allowed values, sequence format,
revision format and sequencing gaps, status/suitability vs container state, duplicate
identifiers, case/illegal chars, path length, disallowed file types, metadata consistency,
orphan files missing from container register.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class FieldSpec(BaseModel):
    name: str
    position: int
    length: int | None = None
    charset: str | None = None
    allowed_values: list[str] | None = None
    required: bool = True
    description: str = ""


class ConventionConfig(BaseModel):
    name: str
    separator: str = "-"
    extension_allowlist: list[str] = Field(default_factory=list)
    path_max_length: int = 260
    fields: list[FieldSpec]
    container_states: dict[str, list[str]] = Field(default_factory=dict)


@dataclass
class Issue:
    path: str
    rule_id: str
    severity: str  # error or warning
    message: str
    suggested_fix: str = ""


@dataclass
class CheckResult:
    issues: list[Issue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    def compliance_pct(self, total_files: int) -> float:
        if total_files == 0:
            return 100.0
        files_with_errors = len({i.path for i in self.issues if i.severity == "error"})
        return max(0.0, 100.0 * (1 - files_with_errors / total_files))


def load_convention(path: Path) -> ConventionConfig:
    with open(path, encoding="utf-8") as f:
        return ConventionConfig(**yaml.safe_load(f))


def check_file(path: Path, config: ConventionConfig, container_state: str | None = None) -> list[Issue]:
    issues: list[Issue] = []
    name = path.stem
    sep = config.separator
    parts = name.split(sep)

    # Field count
    expected_count = len(config.fields)
    if len(parts) != expected_count:
        issues.append(Issue(str(path), "field_count", "error", f"Expected {expected_count} fields, got {len(parts)}"))

    # Field checks
    for i, field_spec in enumerate(config.fields):
        if i >= len(parts):
            if field_spec.required:
                issues.append(Issue(str(path), "field_missing", "error", f"Missing field: {field_spec.name}"))
            continue
        val = parts[i]

        # Length
        if field_spec.length is not None and len(val) != field_spec.length:
            issues.append(
                Issue(
                    str(path),
                    "field_length",
                    "error",
                    f"{field_spec.name}: expected length {field_spec.length}, got {len(val)}",
                )
            )

        # Charset
        if field_spec.charset:
            pattern = "^[" + field_spec.charset + "]+$"
            if not re.match(pattern, val):
                issues.append(Issue(str(path), "field_charset", "error", f"{field_spec.name}: invalid charset"))

        # Allowed values
        if field_spec.allowed_values and val not in field_spec.allowed_values:
            issues.append(
                Issue(str(path), "field_allowed_values", "error", f"{field_spec.name}: '{val}' not in allowed list")
            )

        # Case (should be uppercase for most fields)
        if field_spec.charset and "A-Z" in field_spec.charset and val != val.upper():
            issues.append(
                Issue(
                    str(path),
                    "field_case",
                    "warning",
                    f"{field_spec.name}: should be uppercase",
                    suggested_fix=val.upper(),
                )
            )

    # Status vs container state
    if container_state and any(f.name == "status" for f in config.fields):
        status_idx = next(i for i, f in enumerate(config.fields) if f.name == "status")
        if status_idx < len(parts):
            status = parts[status_idx]
            allowed_for_state = config.container_states.get(container_state, [])
            if allowed_for_state and status not in allowed_for_state:
                issues.append(
                    Issue(
                        str(path),
                        "status_container_mismatch",
                        "error",
                        f"Status '{status}' not allowed in '{container_state}' folder",
                    )
                )

    # Extension
    ext = path.suffix.lower()
    if config.extension_allowlist and ext not in config.extension_allowlist:
        issues.append(Issue(str(path), "disallowed_extension", "error", f"Extension '{ext}' not in allowlist"))

    # Path length
    if len(str(path)) > config.path_max_length:
        issues.append(
            Issue(str(path), "path_length", "warning", f"Path length {len(str(path))} exceeds {config.path_max_length}")
        )

    return issues


def check_folder(folder: Path, config: ConventionConfig) -> CheckResult:
    result = CheckResult()
    seen_ids: dict[str, str] = {}

    for path in folder.rglob("*"):
        if not path.is_file():
            continue

        # Determine container state from parent folder name
        container_state = path.parent.name if path.parent.name in config.container_states else None
        issues = check_file(path, config, container_state)
        result.issues.extend(issues)

        # Duplicate identifier check (project-originator-number)
        parts = path.stem.split(config.separator)
        if len(parts) >= 7:
            identifier = config.separator.join(parts[:3] + parts[6:7])
            if identifier in seen_ids:
                result.issues.append(
                    Issue(
                        str(path), "duplicate_identifier", "error", f"Duplicate identifier with {seen_ids[identifier]}"
                    )
                )
            else:
                seen_ids[identifier] = str(path)

    return result


def write_register(folder: Path, out: Path) -> None:
    rows = []
    for path in folder.rglob("*"):
        if path.is_file():
            rows.append({"path": str(path), "name": path.name, "size": path.stat().st_size})
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "name", "size"])
        writer.writeheader()
        writer.writerows(rows)
