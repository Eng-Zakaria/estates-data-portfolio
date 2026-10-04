"""Reference maps + fuzzy suggestions for unmapped values."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    from rapidfuzz import process as _process

    HAS_RAPIDFUZZ = True
    process = _process
except Exception:  # pragma: no cover
    HAS_RAPIDFUZZ = False
    process = None  # type: ignore[assignment]


def refs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "refs"


def load_map(name: str) -> dict[str, str]:
    df = pd.read_csv(refs_dir() / name, dtype=str)
    return dict(zip(df.iloc[:, 0].str.strip(), df.iloc[:, 1].str.strip()))


def suggest(value: str, choices: list[str], limit: int = 3) -> list[str]:
    if HAS_RAPIDFUZZ:
        assert process is not None
        hits = process.extract(value, choices, limit=limit)
        return [h[0] for h in hits if h[1] >= 60]
    from difflib import get_close_matches

    return get_close_matches(value, choices, n=limit, cutoff=0.6)


def building_crosswalk(truth_buildings: pd.DataFrame) -> dict[str, str]:
    """Exact name → id from truth (synthetic). Fuzzy handled at silver time with suggestions."""
    return dict(zip(truth_buildings.building_name.astype(str), truth_buildings.building_id.astype(str)))
