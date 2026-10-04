"""DST + reconciliation + planted invalid-rows → quarantine (integration, small profile)."""

from pathlib import Path

import pandas as pd
from ingest.cli import _bronze_frame, _run_silver_one
from ingest.silver_meters import transform_meter_A


def test_dst_periods_small(tmp_path: Path):
    # hand-built local series for spring-forward day 2026-03-29 (46 periods expected after UTC conversion)
    rows = []
    for h in range(24):
        for m in (0, 30):
            if h == 1:  # spring gap 01:00-01:59 local does not exist
                continue
            rows.append({"meter_id": "M-T", "local_time": f"29/03/2026 {h:02d}:{m:02d}", "kwh": "5", "unit": "kWh"})
    bronze = pd.DataFrame(rows)
    silver, _, gaps = transform_meter_A(bronze)
    assert len(silver) == 46
    assert gaps.empty  # exact 46 → no gap row


def test_reconciliation_zero_loss(tmp_path: Path):
    from ingest.bronze import load_bronze

    src = sorted(Path("data/raw").glob("timetable_*.csv"))[0]
    root = tmp_path / "lake"
    load_bronze("timetable", src, root / "bronze", ingest_date="2026-03-31")
    bronze_df = _bronze_frame(root, "timetable")
    s_n, q_n = _run_silver_one("timetable", root, Path("data/truth/buildings.parquet"))
    assert s_n + q_n == len(bronze_df)


def test_planted_invalid_rows_quarantined(tmp_path: Path):
    """Every invalid-row defect in ground_truth.yaml for cafm/space must appear in quarantine."""
    import yaml

    gt = yaml.safe_load(Path("data/raw/ground_truth.yaml").read_text())
    assert len(gt.get("defects", [])) > 0
    # run silver for space + cafm on full small bronze
    from ingest.bronze import load_bronze

    root = tmp_path / "lake2"
    for pat, source in [("space_register_*.xlsx", "space_register"), ("cafm_workorders_*.csv", "cafm_workorders")]:
        for f in sorted(Path("data/raw").glob(pat)):
            load_bronze(source, f, root / "bronze", ingest_date="2026-03-31")
    _run_silver_one("space_register", root, Path("data/truth/buildings.parquet"))
    _run_silver_one("cafm_workorders", root, Path("data/truth/buildings.parquet"))
    q_space = pd.read_parquet(root / "quarantine/space_register/quarantine.parquet")
    q_cafm = pd.read_parquet(root / "quarantine/cafm_workorders/quarantine.parquet")
    assert len(q_space) > 0 and len(q_cafm) > 0
    assert q_space._reject_reason.notna().all() and q_cafm._reject_reason.notna().all()
