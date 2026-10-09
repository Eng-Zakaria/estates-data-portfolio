"""P15 point registry generator.

Builds the canonical point list that Node-RED maps topics onto, writes it to
`src/point_registry.csv`, and exposes it to the simulator so both sides agree
on point_id / unit / plausible range.

Naming convention (see docs/point-naming.md):
    point_id = <building>.<equipment>.<point_class>
    topic    = campus/<building>/<system>/<point_class>

`source_address` is a SYNTHETIC placeholder shaped like a BACnet-style
object reference. It is not a real device address and must not be treated as
authoritative: in a live deployment the point_id to device/object mapping
comes from the site's BACnet object list (see docs/mapping-to-real-systems.md).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

BUILDINGS = ["B001", "B003", "B007"]

# equipment kind -> (system topic segment, point classes)
EQUIPMENT_TEMPLATE: dict[str, tuple[str, list[str]]] = {
    "ahu": ("ahu", ["supply_temp", "return_temp", "damper_pos", "fan_speed", "heating_valve", "cooling_valve", "sub_meter_kwh"]),
    "boiler": ("boiler", ["supply_temp", "heating_valve", "sub_meter_kwh"]),
    "pump": ("pump", ["sub_meter_kwh"]),
}

# 8 plant items per building -> 24 total; 17 rooms per building -> 51 total.
# Three AHUs per building, not two: the valve faults need disjoint equipment
# (a stuck heating valve on the same AHU as a planted heat/cool fault makes the
# two faults indistinguishable).
PLANT_ITEMS = {
    "ahu": ["ahu_01", "ahu_02", "ahu_03"],
    "boiler": ["boiler_01", "boiler_02"],
    "pump": ["pump_01", "pump_02", "pump_03"],
}
ROOMS_PER_BUILDING = 17

ROOM_POINT_CLASSES = ["room_temp", "setpoint", "co2", "occupancy"]

# canonical unit per point class; kept in sync with
# contracts/validation_rules.json (tests assert the two agree)
POINT_UNITS: dict[str, str] = {
    "supply_temp": "C",
    "return_temp": "C",
    "room_temp": "C",
    "setpoint": "C",
    "damper_pos": "%",
    "fan_speed": "%",
    "heating_valve": "%",
    "cooling_valve": "%",
    "co2": "ppm",
    "occupancy": "count",
    "sub_meter_kwh": "kWh",
}


def build_registry() -> list[dict[str, str]]:
    """Return the deterministic point registry rows (sorted for stable diffs)."""
    rows: list[dict[str, str]] = []
    for building in BUILDINGS:
        for kind, equipment_ids in PLANT_ITEMS.items():
            system, classes = EQUIPMENT_TEMPLATE[kind]
            for equipment in equipment_ids:
                for point_class in classes:
                    rows.append(_row(building, equipment, kind, system, point_class, "ai"))
        for idx in range(1, ROOMS_PER_BUILDING + 1):
            equipment = f"room_{idx:02d}"
            for point_class in ROOM_POINT_CLASSES:
                # occupancy counts come from a binary/analog input too, but is
                # modelled as AI for uniformity of the synthetic registry
                rows.append(_row(building, equipment, "room", "room", point_class, "ai"))
    return sorted(rows, key=lambda r: r["point_id"])


def _row(building: str, equipment: str, kind: str, system: str, point_class: str, obj_type: str) -> dict[str, str]:
    point_id = f"{building}.{equipment}.{point_class}"
    return {
        "point_id": point_id,
        "building": building,
        "system": system,
        "equipment": equipment,
        "equipment_kind": kind,
        "point_class": point_class,
        "unit": POINT_UNITS[point_class],
        # the equipment segment is required: `campus/B001/ahu/cooling_valve` is
        # shared by ahu_01 and ahu_02, so without it a topic cannot resolve to
        # a single canonical point_id
        "topic": f"campus/{building}/{system}/{equipment}/{point_class}",
        "source_address": f"SYNTH/{building}/{equipment.upper()}/{obj_type.upper()}.{point_class}",
    }


def write_registry(path: Path) -> list[dict[str, str]]:
    rows = build_registry()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("projects/p15-bms-iot/src/point_registry.csv"))
    args = parser.parse_args()
    rows = write_registry(args.out)
    systems = {r["system"] for r in rows}
    print(f"Wrote {len(rows)} points across {len(systems)} systems to {args.out}")


if __name__ == "__main__":
    main()
