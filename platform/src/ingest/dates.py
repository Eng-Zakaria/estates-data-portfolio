"""Explicit date parsing with candidate logging (no silent coercion)."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

CANDIDATES = [
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%d-%b-%y %H:%M",
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%Y-%m-%d %H:%M",
]


def parse_with_candidates(s: pd.Series, candidates: list[str] | None = None) -> tuple[pd.Series, pd.Series]:
    """Return (parsed datetime64[ns, UTC-naive], matched_format). Unparseable → NaT, format 'unparseable'.

    Excel serials (numbers 20000-60000) are converted via 1899-12-30 base.
    """
    cands = candidates or CANDIDATES
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    fmt = pd.Series("unparseable", index=s.index, dtype=object)
    remaining = s.copy()
    # Excel serials first
    num = pd.to_numeric(remaining, errors="coerce")
    is_serial = num.between(20000, 60000)
    if is_serial.any():
        base = datetime(1899, 12, 30)
        out[is_serial] = [base + pd.Timedelta(days=float(v)) for v in num[is_serial]]
        fmt[is_serial] = "excel_serial"
        remaining = remaining[~is_serial]
    else:
        remaining = remaining[remaining.notna()]
    for c in cands:
        if remaining.empty:
            break
        try:
            p = pd.to_datetime(remaining, format=c, errors="coerce")
        except Exception:
            continue
        hit = p.notna()
        if hit.any():
            out.loc[hit.index[hit]] = p[hit].to_numpy()
            fmt.loc[hit.index[hit]] = c
            remaining = remaining[~hit]
    return out, fmt
