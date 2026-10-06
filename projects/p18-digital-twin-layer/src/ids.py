"""Canonical ID definitions and validation (P18)."""

from __future__ import annotations

import re

# Canonical ID prefixes (namespace:local-id)
PREFIXES = {
    "bldg": r"^B\d{3}$",           # e.g., B001
    "space": r"^S-B\d{3}-L\d{2}-\d{3}$",  # e.g., S-B001-L00-001
    "asset": r"^A-B\d{3}-\d{6}$",  # e.g., A-B001-000001
    "meter": r"^M-B\d{3}-[EGH]\d{2}$",    # e.g., M-B001-E01
    "sensor": r"^SN-\d{4}$",       # e.g., SN-0001
    "bms_point": r"^SN-\d{4} \[(ppm|°C|%)\]$",  # e.g., SN-0001 [ppm]
    "ifc": r"^[0-9A-Za-z_$]{22}$", # IFC GlobalId (base64-ish, 22 chars)
}

# Compiled regex
_COMPILED = {k: re.compile(v) for k, v in PREFIXES.items()}


def validate_canonical_id(cid: str) -> tuple[bool, str | None]:
    """Validate a canonical ID format. Returns (is_valid, prefix_or_none)."""
    if ":" not in cid:
        return False, None
    prefix, local = cid.split(":", 1)
    if prefix not in _COMPILED:
        return False, None
    if not _COMPILED[prefix].match(local):
        return False, None
    return True, prefix


def make_canonical(prefix: str, local: str) -> str:
    """Construct a canonical ID. Validates prefix and local."""
    if prefix not in PREFIXES:
        raise ValueError(f"Unknown prefix: {prefix}")
    if not _COMPILED[prefix].match(local):
        raise ValueError(f"Local part {local!r} does not match {prefix} pattern")
    return f"{prefix}:{local}"


def parse_canonical(cid: str) -> tuple[str, str] | None:
    """Parse canonical ID into (prefix, local). Returns None if invalid."""
    ok, prefix = validate_canonical_id(cid)
    if not ok:
        return None
    return prefix, cid.split(":", 1)[1]


# System names for crosswalk
SYSTEMS = [
    "space_register",
    "cafm",
    "ifc",
    "bms",
    "meter",
    "sensor",
    "timetable",
    "work_order",
    "inspection",
]