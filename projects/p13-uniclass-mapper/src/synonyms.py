"""Synonym store for the P13 active-learning loop.

`synonyms.csv` maps a free-text phrase to a Uniclass code. Rows come from human
review overrides (review UI) or manual curation. The matcher applies a bounded
bonus when a phrase appears in the query, and records the hit in
`matched_terms` so decisions stay explainable.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

DEFAULT_SYNONYMS_PATH = Path(__file__).resolve().parents[1] / "data" / "synonyms.csv"

# Bonus added to the fuzzy (0-100) score on a phrase hit. Bounded so a synonym
# can rescue a correct code but cannot outvote overwhelming evidence.
SYNONYM_BONUS = 12.0
SYNONYM_BONUS_CAP = 100.0

# Bonus added to the hybrid (0-1) score on a phrase hit. Curated and
# human-reviewed synonyms are trusted signals, on par with equipment tags.
# Sized (0.25) to outvote parent/cousin titles that share one word ("emergency"
# vs "energy", "heating" vs "Heat emitters") without overriding a confident
# cross-table match — every seeded phrase is unique to one label's rows.
SYNONYM_HYBRID_BONUS = 0.25


def _default_path() -> Path:
    return DEFAULT_SYNONYMS_PATH


def load_synonyms(path: str | Path | None = None) -> pd.DataFrame:
    """Load synonyms.csv, returning an empty frame with the right columns."""
    p = Path(path) if path else _default_path()
    if not p.exists():
        return pd.DataFrame(columns=["phrase", "code"])
    df = pd.read_csv(p, dtype=str).fillna("")
    for col in ("phrase", "code"):
        if col not in df.columns:
            df[col] = ""
    # Legacy files used a "synonym" column; accept both.
    if (df["phrase"] == "").all() and "synonym" in df.columns:
        df["phrase"] = df["synonym"]
    return df[["phrase", "code"]]


@lru_cache(maxsize=8)
def _cached_phrases(path_str: str) -> tuple[tuple[str, str], ...]:
    df = load_synonyms(path_str)
    rows = [
        (str(phrase).lower().strip(), str(code).strip())
        for phrase, code in zip(df["phrase"], df["code"])
        if str(phrase).strip() and str(code).strip()
    ]
    return tuple(rows)


def synonym_hits(query: str, path: str | Path | None = None) -> list[tuple[str, str]]:
    """Return (phrase, code) pairs whose phrase appears in the query."""
    key = str(Path(path) if path else _default_path())
    q = query.lower()
    return [(phrase, code) for phrase, code in _cached_phrases(key) if phrase in q]


def clear_synonym_cache() -> None:
    _cached_phrases.cache_clear()


def record_decision(
    description: str,
    human_code: str,
    path: str | Path | None = None,
) -> None:
    """Append a human override to synonyms.csv (dedup on identical rows)."""
    p = Path(path) if path else _default_path()
    phrase = " ".join(description.lower().split())
    code = human_code.strip()
    if not phrase or not code:
        raise ValueError("description and human_code must both be non-empty")
    if p.exists():
        df = pd.read_csv(p, dtype=str).fillna("")
    else:
        df = pd.DataFrame(columns=["phrase", "code"])
    if "phrase" not in df.columns and "synonym" in df.columns:
        df = df.rename(columns={"synonym": "phrase"})
    dup = ((df.get("phrase", "") == phrase) & (df.get("code", "") == code)).any()
    if not bool(dup):
        df = pd.concat([df, pd.DataFrame([{"phrase": phrase, "code": code}])], ignore_index=True)
        p.parent.mkdir(parents=True, exist_ok=True)
        df[["phrase", "code"]].to_csv(p, index=False)
    clear_synonym_cache()
