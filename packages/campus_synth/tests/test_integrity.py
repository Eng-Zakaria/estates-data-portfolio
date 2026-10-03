"""Referential integrity on clean truth: zero orphans."""

import pandas as pd


def test_no_orphans(small_truth):
    t, _ = small_truth
    buildings = set(t["buildings"].building_id)
    spaces = set(t["spaces"].space_id)
    assets = set(t["assets"].asset_id)
    floors = set(t["floors"].floor_id)
    depts = set(t["departments"].department_id)

    assert set(t["floors"].building_id) <= buildings
    assert set(t["spaces"].building_id) <= buildings
    assert set(t["spaces"].floor_id) <= floors
    assert set(t["spaces"].department_id) <= depts
    assert set(t["assets"].building_id) <= buildings
    assert set(t["assets"].space_id) <= spaces
    assert set(t["work_orders"].asset_id) <= assets
    assert set(t["work_orders"].building_id) <= buildings
    assert set(t["meters"].building_id) <= buildings
    assert set(t["sensors"].space_id) <= spaces
    assert set(t["sensor_readings"].sensor_id) <= set(t["sensors"].sensor_id)
    assert set(t["meter_readings_hh"].meter_id) <= set(t["meters"].meter_id)
    assert set(t["timetable_events"].space_id) <= spaces


def test_space_nia_lte_gia(small_truth):
    t, _ = small_truth
    gia = dict(zip(t["buildings"].building_id, t["buildings"].gia_m2))
    sums: pd.Series = t["spaces"].groupby("building_id")["nia_m2"].sum()
    for bid, tot in sums.items():
        assert tot <= gia[bid] * 1.0001, bid
