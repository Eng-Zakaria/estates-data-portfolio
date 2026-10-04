"""Silver quarantine: each rule type has pass + fail fixtures."""

import pandas as pd
from ingest.silver_cafm import transform_cafm
from ingest.silver_meters import cumulative_to_interval
from ingest.silver_space import transform_space


def _truth_b():
    return pd.DataFrame([{"building_name": "Building A", "building_id": "B001"}])


def test_space_quarantine_reasons():
    bronze = pd.DataFrame(
        [
            {
                "building_name": "Building A",
                "Room": "R1",
                "category_messy": "Teaching",
                "area_text": "20 m2",
                "Seats": "10",
            },
            {"building_name": None, "Room": "R2", "category_messy": "Teaching", "area_text": "20 m2", "Seats": "10"},
            {
                "building_name": "Building A",
                "Room": "R3",
                "category_messy": "Nope",
                "area_text": "20 m2",
                "Seats": "10",
            },
            {
                "building_name": "Building A",
                "Room": "R4",
                "category_messy": "Teaching",
                "area_text": "-5 m2",
                "Seats": "10",
            },
            {
                "building_name": "Building A",
                "Room": "R1",
                "category_messy": "Teaching",
                "area_text": "20 m2",
                "Seats": "10",
            },
        ]
    )
    silver, quar, unmapped = transform_space(bronze, _truth_b())
    assert len(silver) == 1
    assert len(quar) == 4
    assert any("nulls" in r for r in quar._reject_reason)
    assert any("unmapped" in r for r in quar._reject_reason)
    assert any("out_of_range" in r for r in quar._reject_reason)
    assert any("duplicate" in r for r in quar._reject_reason)
    assert len(unmapped) >= 1


def test_cafm_completed_order_and_cost():
    bronze = pd.DataFrame(
        [
            {
                "WO_Number": "W1",
                "AssetRef": "A1",
                "space_id": "S",
                "building_id": "B001",
                "wo_type": "Reactive",
                "priority": "P2",
                "Raised": "01/02/2026 09:00",
                "target_ts": None,
                "started_ts": None,
                "Completed": "01/02/2026 10:00",
                "Status": "Complete",
                "trade": "Mech",
                "contractor": "Alpha",
                "labour_hours": "2",
                "Cost": "£100.00",
                "fault_code": "F",
                "description": "d",
            },
            {
                "WO_Number": "W2",
                "AssetRef": "A1",
                "space_id": "S",
                "building_id": "B001",
                "wo_type": "Reactive",
                "priority": "P2",
                "Raised": "01/02/2026 09:00",
                "target_ts": None,
                "started_ts": None,
                "Completed": "01/02/2026 09:00",
                "Status": "Complete",
                "trade": "Mech",
                "contractor": "Alpha",
                "labour_hours": "2",
                "Cost": "£100.00",
                "fault_code": "F",
                "description": "d",
            },
            {
                "WO_Number": "W3",
                "AssetRef": "A1",
                "space_id": "S",
                "building_id": "B001",
                "wo_type": "Reactive",
                "priority": "P2",
                "Raised": "01/02/2026 09:00",
                "target_ts": None,
                "started_ts": None,
                "Completed": None,
                "Status": "Open",
                "trade": "Mech",
                "contractor": "Alpha",
                "labour_hours": "2",
                "Cost": "£-5.00",
                "fault_code": "F",
                "description": "d",
            },
        ]
    )
    silver, quar = transform_cafm(bronze)
    assert len(silver) == 1
    assert any("completed_before_raised" in r for r in quar._reject_reason)
    assert any("negative_cost" in r for r in quar._reject_reason)


def test_cumulative_rollover():
    s = pd.Series([99990.0, 99995.0, 5.0, 15.0])
    iv, was, ro = cumulative_to_interval(s)
    assert was is True
    assert ro is not None
    assert iv.iloc[2] > 0
    s2 = pd.Series([10.0, 12.0, 9.0, 14.0])
    _, was2, _ = cumulative_to_interval(s2)
    assert was2 is False
