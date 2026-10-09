"""Point registry: the mapping between topic, point_id and unit."""

from __future__ import annotations

import re

from conftest import REGISTRY_CSV
from make_registry import BUILDINGS, PLANT_ITEMS, ROOMS_PER_BUILDING, build_registry


def test_registry_size_matches_the_spec():
    """~20 plant items and ~50 rooms across 3 buildings."""
    rows = build_registry()
    plant = [r for r in rows if r["equipment_kind"] != "room"]
    rooms = [r for r in rows if r["equipment_kind"] == "room"]
    # 8 plant items per building (3 AHU, 2 boilers, 3 pumps) across 3 buildings
    assert len({(r["building"], r["equipment"]) for r in plant}) == 24
    assert len({(r["building"], r["equipment"]) for r in rooms}) == 51  # 17 rooms x 3 buildings
    assert len(rows) == len(plant) + len(rooms)
    assert {r["building"] for r in rows} == set(BUILDINGS)


def test_point_ids_are_unique_and_follow_the_naming_convention():
    ids = [r["point_id"] for r in build_registry()]
    assert len(ids) == len(set(ids))
    for row in build_registry():
        assert row["point_id"] == f"{row['building']}.{row['equipment']}.{row['point_class']}"
        assert re.fullmatch(r"[A-Z0-9]+\.[a-z0-9_]+\.[a-z0-9_]+", row["point_id"])


def test_topics_are_unique_per_point():
    """The whole lookup in Node-RED is topic -> point_id, so it must be 1:1.

    A topic without the equipment segment is shared by every AHU in a building,
    which silently collapses 294 points onto 45 topics.
    """
    topics = [r["topic"] for r in build_registry()]
    assert len(topics) == len(set(topics))


def test_topic_matches_the_contract_pattern(registry, rules):
    pattern = re.compile(rules["topic_pattern"])
    for row in registry.values():
        assert pattern.fullmatch(row["topic"]), row["topic"]


def test_committed_registry_matches_the_generator():
    """src/point_registry.csv is committed, so it must not drift from the code."""
    import csv

    from validate import load_registry

    committed = load_registry(str(REGISTRY_CSV))
    assert committed == {r["point_id"]: r for r in build_registry()}


def test_source_address_is_labelled_synthetic():
    """source_address must not read as a real device address."""
    for row in load_rows():
        assert row["source_address"].startswith("SYNTH/")


def test_every_point_class_has_a_contract_range_and_a_registry_unit(registry, rules):
    from make_registry import POINT_UNITS

    for point_id, row in registry.items():
        rule = rules["rules_by_point_class"].get(row["point_class"])
        assert rule is not None, f"{point_id} has no contract rule"
        assert row["unit"] == rule["unit"] == POINT_UNITS[row["point_class"]]
        assert rule["min"] <= rule["max"]


def test_room_points_and_plant_points_are_present(registry):
    classes = {r["point_class"] for r in registry.values()}
    assert {"room_temp", "setpoint", "co2", "occupancy"} <= classes
    assert {"supply_temp", "return_temp", "damper_pos", "fan_speed", "sub_meter_kwh"} <= classes


def test_rooms_per_building_is_consistent():
    assert ROOMS_PER_BUILDING == 17
    assert sum(len(v) for v in PLANT_ITEMS.values()) == 8


def load_rows() -> list[dict[str, str]]:
    import csv

    with REGISTRY_CSV.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))