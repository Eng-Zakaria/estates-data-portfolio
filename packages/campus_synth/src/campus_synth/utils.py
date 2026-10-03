"""Deterministic RNG, IDs, IFC GUIDs, UK time helpers."""

from __future__ import annotations

import hashlib
import string
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

LONDON = ZoneInfo("Europe/London")
UTC = UTC

_IFC_ALPHABET = string.ascii_letters + string.digits + "_$"


def make_rng(seed: int) -> np.random.Generator:
    """Single seeded Generator for all randomness (spec hard rule)."""
    return np.random.default_rng(seed)


def ifc_guid(rng: np.random.Generator) -> str:
    """Fake 22-char IFC GlobalId (base64-style). Not a real IFC compression, labelled synthetic."""
    chars = rng.choice(list(_IFC_ALPHABET), size=22)
    return "".join(chars)


def start_date_for(end: date, n_months: int) -> date:
    """First day of the window ending on `end` spanning n_months back (inclusive logic)."""
    # e.g. end 2026-03-31, n=3 -> 2026-01-01 ; n=24 -> 2024-04-01
    y, m = end.year, end.month
    m -= n_months - 1
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, 1)


def hh_index_utc(start: date, end: date) -> pd.DatetimeIndex:
    """Half-hourly UTC index [start 00:00, end 23:30]. Stored timezone-aware UTC."""
    s = pd.Timestamp(start, tz="UTC")
    e = pd.Timestamp(end, tz="UTC") + pd.Timedelta(days=1) - pd.Timedelta(minutes=30)
    return pd.date_range(s, e, freq="30min", tz="UTC")


def to_london(ts: pd.DatetimeIndex | pd.Series) -> pd.DatetimeIndex | pd.Series:
    """Convert UTC timestamps to Europe/London for source-system exports."""
    return ts.tz_convert(LONDON)


def local_period_counts_2025() -> dict[str, int]:
    """Reference: 2025 UK DST days (used in tests)."""
    return {"2025-03-30": 46, "2025-10-26": 50, "2025-01-15": 48}


def hash_frame(df: pd.DataFrame) -> str:
    """Stable hash of a frame: sort rows+cols, CSV with fixed float format."""
    d = df.copy()
    d = d.reindex(sorted(d.columns), axis=1).sort_values(list(sorted(d.columns))).reset_index(drop=True)
    # normalise datetimes to iso strings for stability
    for c in d.columns:
        if pd.api.types.is_datetime64_any_dtype(d[c]) or getattr(d[c].dtype, "tz", None) is not None:
            d[c] = pd.to_datetime(d[c], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    csv = d.to_csv(index=False, float_format="%.6f")
    return hashlib.sha256(csv.encode()).hexdigest()


def date_to_ts(d: date) -> pd.Timestamp:
    """Midnight UTC timestamp for a date."""
    return pd.Timestamp(datetime(d.year, d.month, d.day, tzinfo=UTC))
