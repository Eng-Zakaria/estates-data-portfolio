"""Bronze idempotency: same sha → skipped; corrected file → new ingest_id."""

from pathlib import Path

from ingest.bronze import load_bronze


def test_bronze_idempotent(tmp_path: Path):
    src = sorted(Path("data/raw").glob("timetable_*.csv"))[0]
    out = tmp_path / "lake"
    dest1, e1 = load_bronze("timetable", src, out / "bronze", ingest_date="2026-03-31")
    assert e1["status"] == "loaded"
    dest2, e2 = load_bronze("timetable", src, out / "bronze", ingest_date="2026-03-31")
    assert e2["status"] == "skipped"
    assert dest1 == dest2
    # corrected file (append a row) → new ingest
    import pandas as pd

    df = pd.read_csv(src, dtype=str)
    df2 = pd.concat([df, df.iloc[:1]], ignore_index=True)
    corr = tmp_path / "timetable_corr.csv"
    df2.to_csv(corr, index=False)
    _, e3 = load_bronze("timetable", corr, out / "bronze", ingest_date="2026-03-31")
    assert e3["status"] == "loaded"
    assert e3["ingest_id"] != e1["ingest_id"]
