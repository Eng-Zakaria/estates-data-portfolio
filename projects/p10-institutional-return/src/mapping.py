"""Mapping layer: internal space categories → return categories (P10).

Versioned config table; test that every internal category maps exactly once.
"""

from __future__ import annotations

from pathlib import Path

INTERNAL_TO_RETURN = {
    "Teaching": "Teaching",
    "Office": "Research",  # office space → research support
    "Laboratory": "Research",
    "Library": "Teaching",
    "Residential": "Residential",
    "Catering": "Other",
    "Sports": "Other",
    "Support": "Other",
}

# Reverse map for validation
RETURN_CATEGORIES = sorted(set(INTERNAL_TO_RETURN.values()))


def get_return_category(internal: str) -> str | None:
    """Map internal category to return category."""
    return INTERNAL_TO_RETURN.get(internal)


def validate_mapping() -> tuple[bool, list[str]]:
    """Check every internal category maps exactly once."""
    errors = []
    seen = set()
    for internal, ret in INTERNAL_TO_RETURN.items():
        if internal in seen:
            errors.append(f"Duplicate internal category: {internal}")
        seen.add(internal)
        if ret not in RETURN_CATEGORIES:
            errors.append(f"Unknown return category: {ret}")
    # All 8 internal categories must be present
    expected = {"Teaching", "Office", "Laboratory", "Library", "Residential", "Catering", "Sports", "Support"}
    missing = expected - set(INTERNAL_TO_RETURN.keys())
    if missing:
        errors.append(f"Missing mappings for: {missing}")
    return len(errors) == 0, errors


def write_mapping_csv(out: Path) -> None:
    """Write mapping table for audit/review."""
    import csv
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["internal_category", "return_category", "version", "notes"])
        for internal, ret in sorted(INTERNAL_TO_RETURN.items()):
            w.writerow([internal, ret, "v1", "Illustrative mapping; not official HESA/TRAC codes"])