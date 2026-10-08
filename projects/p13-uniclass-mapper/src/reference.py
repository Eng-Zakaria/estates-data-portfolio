"""Load and provide access to Uniclass 2015 reference data (P13).

Loads the official CSV (or mock placeholder) and provides lookup by code,
title search, and hierarchy traversal.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd

OFFICIAL_CSV = Path(__file__).resolve().parents[1] / "data" / "uniclass_2015.csv"
MOCK_CSV = Path(__file__).resolve().parents[1] / "data" / "mock_uniclass_dev_placeholder.csv"


def load_uniclass() -> pd.DataFrame:
    """Load the Uniclass table (official or mock).

    Returns DataFrame with columns: code, title, level, parent_code, table, version, source_url, retrieved_date, is_mock
    """
    csv_path = Path(__file__).resolve().parents[1] / "data" / "uniclass_2015.csv"
    if not csv_path.exists():
        # Try mock as fallback
        csv_path = MOCK_CSV
    if not csv_path.exists():
        raise FileNotFoundError(
            f"No Uniclass CSV found at "
            f"{Path(__file__).resolve().parents[1] / 'data' / 'uniclass_2015.csv'} or {MOCK_CSV}"
        )

    df = pd.read_csv(csv_path, comment="#", dtype=str).fillna("")
    # Ensure expected columns
    expected = ["code", "title", "level", "parent_code", "table", "version", "source_url", "retrieved_date", "is_mock"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    return df


@lru_cache(maxsize=1)
def get_uniclass_df() -> pd.DataFrame:
    return load_uniclass()


def get_codes(table: str | None = None) -> list[str]:
    """Return all codes, optionally filtered by table ('Products' or 'Systems')."""
    df = get_uniclass_df()
    if table:
        df = df[df["table"] == table]
    return sorted(df["code"].unique().tolist())


def get_title(code: str) -> str | None:
    """Return the title for a code, or None if not found."""
    df = get_uniclass_df()
    row = df[df["code"] == code]
    if row.empty:
        return None
    return row.iloc[0]["title"]


def get_level(code: str) -> int | None:
    """Return the hierarchy level for a code (1=top, 2=group, 3=element...)."""
    df = get_uniclass_df()
    row = df[df["code"] == code]
    if row.empty:
        return None
    try:
        return int(row.iloc[0]["level"])
    except ValueError:
        return None


def get_parent(code: str) -> str | None:
    """Return the parent code, or None if top-level."""
    df = get_uniclass_df()
    row = df[df["code"] == code]
    if row.empty:
        return None
    return row.iloc[0]["parent_code"] or None


def get_children(code: str) -> list[str]:
    """Return direct children codes."""
    df = get_uniclass_df()
    return sorted(df[df["parent_code"] == code]["code"].unique().tolist())


def get_descendants(code: str, max_level: int | None = None) -> list[str]:
    """Return all descendant codes (recursive)."""
    children = get_children(code)
    all_desc = list(children)
    for child in children:
        all_desc.extend(get_descendants(child, max_level))
    if max_level:
        # Filter by level
        df = get_uniclass_df()
        level_map = dict(zip(df["code"], df["level"].astype(int)))
        base_level = level_map.get(code, 0)
        all_desc = [c for c in all_desc if level_map.get(c, 0) <= base_level + max_level]
    return all_desc


def get_subtree_codes(code: str) -> list[str]:
    """Return code + all descendants (for sub-tree filtering)."""
    return [code] + get_descendants(code)


def search_titles(query: str, table: str | None = None, limit: int = 20) -> list[dict]:
    """Simple title search (case-insensitive substring match)."""
    df = get_uniclass_df()
    if table:
        df = df[df["table"] == table]
    mask = df["title"].str.contains(query, case=False, na=False)
    results = df[mask].head(limit)
    return results[["code", "title", "level", "table"]].to_dict("records")


def is_mock() -> bool:
    """Check if the loaded data is the mock placeholder."""
    df = get_uniclass_df()
    return df["is_mock"].astype(bool).any()


def get_warning() -> str:
    """Return a warning message if using mock data."""
    if is_mock():
        return (
            "WARNING: Using NON-AUTHORITATIVE mock Uniclass data (development only). "
            "Official source: https://uniclass.thenbs.com/download (requires login). "
            "See docs/OPEN_QUESTIONS.md for details."
        )
    return ""


if __name__ == "__main__":
    df = load_uniclass()
    print(f"Loaded {len(df)} Uniclass codes")
    print(f"Tables: {df['table'].unique()}")
    print(f"Levels: {sorted(df['level'].astype(int).unique())}")
    print(f"Is mock: {is_mock()}")
    if is_mock():
        print(get_warning())
    print("\nSample Products:")
    print(df[df["table"] == "Products"].head(10)[["code", "title", "level"]].to_string())
    print("\nSample Systems:")
    print(df[df["table"] == "Systems"].head(10)[["code", "title", "level"]].to_string())
