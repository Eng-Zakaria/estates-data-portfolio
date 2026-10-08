"""Fuzzy matching using rapidfuzz (P13)."""

from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz, process
from reference import get_uniclass_df


@dataclass
class FuzzyMatch:
    code: str
    title: str
    score: float
    table: str
    level: int


def fuzzy_match(
    query: str,
    table: str | None = None,
    scorer: str = "token_set_ratio",
    limit: int = 10,
    score_cutoff: float = 0.0,
) -> list[tuple[str, float, int]]:
    """Fuzzy match query against Uniclass titles.

    Returns list of (code, score, index) tuples.

    Matching is case-insensitive (titles are Title Case, queries lowercase):
    both sides are lowered before scoring; indices still map to df rows.
    """
    df = get_uniclass_df()
    if table:
        df = df[df["table"] == table]

    choices = [t.lower() for t in df["title"].tolist()]
    codes = df["code"].tolist()

    # Map scorer name to rapidfuzz function
    scorer_map = {
        "ratio": fuzz.ratio,
        "partial_ratio": fuzz.partial_ratio,
        "token_sort_ratio": fuzz.token_sort_ratio,
        "token_set_ratio": fuzz.token_set_ratio,
        "partial_token_set_ratio": fuzz.partial_token_set_ratio,
        "partial_token_sort_ratio": fuzz.partial_token_sort_ratio,
    }
    scorer_fn = scorer_map.get(scorer, fuzz.token_set_ratio)

    results = process.extract(
        query.lower(),
        choices,
        scorer=scorer_fn,
        limit=limit,
        score_cutoff=score_cutoff,
    )
    return [(codes[idx], score, idx) for _, score, idx in results]


def fuzzy_match_detailed(
    query: str,
    table: str | None = None,
    scorer: str = "token_set_ratio",
    limit: int = 10,
    score_cutoff: float = 0.0,
) -> list[FuzzyMatch]:
    """Fuzzy match returning detailed match objects."""
    raw = fuzzy_match(query, table, scorer, limit, score_cutoff)
    df = get_uniclass_df()
    if table:
        df = df[df["table"] == table]

    matches = []
    for code, score, idx in raw:
        row = df.iloc[idx]
        matches.append(
            FuzzyMatch(
                code=code,
                title=row["title"],
                score=score,
                table=row["table"],
                level=int(row["level"]),
            )
        )
    return matches


def best_fuzzy_match(
    query: str,
    table: str | None = None,
    scorer: str = "token_set_ratio",
    score_cutoff: float = 60.0,
) -> FuzzyMatch | None:
    """Return the single best match above cutoff, or None."""
    matches = fuzzy_match_detailed(query, table, scorer, limit=1, score_cutoff=score_cutoff)
    return matches[0] if matches else None


if __name__ == "__main__":
    # Quick test
    from reference import get_uniclass_df

    df = get_uniclass_df()
    print(f"Total codes: {len(df)}")

    test_queries = [
        "air handling unit",
        "boiler",
        "fan coil unit",
        "vav box",
        "chiller",
        "pump",
        "air condition",
        "lighting",
    ]

    for q in test_queries:
        matches = fuzzy_match_detailed(q, limit=3)
        print(f"\nQuery: '{q}'")
        for m in matches:
            print(f"  {m.code} ({m.title}) - score: {m.score:.1f} [{m.table}]")
