"""DST: spring-forward 46 periods, autumn-back 50 in Europe/London exports."""

from datetime import date

import pandas as pd
from campus_synth.utils import hh_index_utc


def _local_counts(start: date, end: date) -> dict[str, int]:
    idx = hh_index_utc(start, end)
    loc = idx.tz_convert("Europe/London")
    return loc.to_series().dt.date.astype(str).value_counts().to_dict()


def test_dst_2025_known_days():
    counts = _local_counts(date(2025, 3, 29), date(2025, 3, 31))
    assert counts["2025-03-30"] == 46, counts
    counts2 = _local_counts(date(2025, 10, 24), date(2025, 10, 28))
    assert counts2["2025-10-26"] == 50, counts2
    # middle non-DST day is full (edge days excluded — UTC window vs local midnight)
    assert counts2["2025-10-25"] == 48


def test_small_window_spring_forward(small_truth):
    t, _ = small_truth
    # small window 2026-01-01..2026-03-31 includes 2026-03-29 spring forward
    df = t["meter_readings_hh"]
    df = df.copy()
    df["loc"] = pd.to_datetime(df["ts_utc"], utc=True).dt.tz_convert("Europe/London")
    df["ld"] = df["loc"].dt.date.astype(str)
    one = df[df.meter_id == df.meter_id.iloc[0]]
    c = one.groupby("ld").size().to_dict()
    assert c.get("2026-03-29") == 46, {k: v for k, v in c.items() if "03-2" in k}
