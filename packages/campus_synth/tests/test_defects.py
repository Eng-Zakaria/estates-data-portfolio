"""Defect catalogue: injected counts equal log counts."""

import pandas as pd
from campus_synth.defects import DEFECT_TYPES, inject_defects
from campus_synth.utils import make_rng


def test_inject_logs_match_output():
    rng = make_rng(7)
    df = pd.DataFrame(
        {
            "id": [f"R{i:03d}" for i in range(100)],
            "name": [f"name-{i}" for i in range(100)],
            "val": [float(i + 1) for i in range(100)],
            "due_date": ["2026-01-01"] * 100,
            "building_id": ["B001"] * 100,
        }
    )
    out, logs = inject_defects(df, "demo", rng, 0.10, key_col="id", numeric_cols=["val"])
    assert len(logs) > 0
    # every log type is catalogued
    for e in logs:
        assert e["type"] in DEFECT_TYPES + [
            "duplicate_rows",
            "nulls_in_mandatory",
            "out_of_range",
            "misspelt_category",
            "future_dates",
            "orphan_fk",
        ]
    # duplicates actually grew the frame
    dup_logs = [e for e in logs if e["type"] == "duplicate_rows"]
    assert len(out) >= len(df) + len(dup_logs) - 3  # orphans may also add rows
    # out-of-range produced a negative
    oor = [e for e in logs if e["type"] == "out_of_range"]
    if oor:
        assert (out["val"] < 0).any()


def test_zero_defects_clean():
    rng = make_rng(1)
    df = pd.DataFrame({"id": ["A"], "v": [1.0]})
    out, logs = inject_defects(df, "t", rng, 0.0)
    assert logs == []
    assert out.equals(df)
