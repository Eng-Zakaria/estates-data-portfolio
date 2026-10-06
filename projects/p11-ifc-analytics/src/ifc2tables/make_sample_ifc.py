"""Generate a synthetic IFC model for P11 with planted defects matching ground_truth.yaml.

Defects planted:
- Elements without type, classification, or space containment
- Duplicate element names
- Zero-area spaces
- 12 rooms with area diff > 10% from register
- 5 rooms missing from model (match ground_truth.yaml)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import ifcopenshell
import pandas as pd

TRUTH = Path("data/truth")


def load_truth() -> pd.DataFrame:
    return pd.read_parquet(TRUTH / "spaces.parquet")


def load_buildings() -> pd.DataFrame:
    return pd.read_parquet(TRUTH / "buildings.parquet")


def make_sample_ifc(out: Path, building_id: str = "B003") -> None:
    spaces = load_truth()
    buildings = load_buildings()
    bldg = buildings[buildings["building_id"] == building_id].iloc[0]
    bldg_spaces = spaces[spaces["building_id"] == building_id].copy()

    # Plant defects: pick 12 rooms for area mismatch, 5 rooms to omit
    mismatch_rooms = bldg_spaces.sample(n=min(12, len(bldg_spaces)), random_state=42)["room_code"].tolist()
    missing_rooms = (
        bldg_spaces[~bldg_spaces["room_code"].isin(mismatch_rooms)]
        .sample(n=min(5, len(bldg_spaces) - len(mismatch_rooms)), random_state=42)["room_code"]
        .tolist()
    )

    f = ifcopenshell.file(schema="IFC4")
    project = f.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(), Name=f"Campus Estate {building_id}")
    site = f.create_entity("IfcSite", GlobalId=ifcopenshell.guid.new(), Name="Campus")
    building = f.create_entity("IfcBuilding", GlobalId=ifcopenshell.guid.new(), Name=building_id)

    # Storeys from truth if available, else single storey
    storeys = {}
    for _, row in bldg_spaces.iterrows():
        storey_name = row.get("storey", "L00") if "storey" in row else "L00"
        if storey_name not in storeys:
            storeys[storey_name] = f.create_entity(
                "IfcBuildingStorey", GlobalId=ifcopenshell.guid.new(), Name=storey_name
            )

    for storey in storeys.values():
        pass  # created above

    spaces_created = []
    for _, row in bldg_spaces.iterrows():
        room = row["room_code"]
        if room in missing_rooms:
            continue

        storey_name = row.get("storey", "L00") if "storey" in row else "L00"
        storey = storeys.get(storey_name, list(storeys.values())[0])

        area = row["nia_m2"]
        if room in mismatch_rooms:
            area = area * 1.15  # >10% mismatch

        space = f.create_entity("IfcSpace", GlobalId=ifcopenshell.guid.new(), Name=room)
        qto = f.create_entity("IfcElementQuantity", GlobalId=ifcopenshell.guid.new(), Name="Qto_SpaceBaseQuantities")
        area_qty = f.create_entity("IfcQuantityArea", Name="GrossFloorArea", AreaValue=float(area))
        qto.Quantities = [area_qty]
        f.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=[space],
            RelatingPropertyDefinition=qto,
        )

        pset = f.create_entity("IfcPropertySet", GlobalId=ifcopenshell.guid.new(), Name="Pset_SpaceCommon")
        cat_prop = f.create_entity(
            "IfcPropertySingleValue",
            Name="Category",
            NominalValue=f.create_entity("IfcLabel", wrappedValue=row.get("space_category", "Office")),
        )
        pset.HasProperties = [cat_prop]
        f.create_entity(
            "IfcRelDefinesByProperties",
            GlobalId=ifcopenshell.guid.new(),
            RelatedObjects=[space],
            RelatingPropertyDefinition=pset,
        )

        spaces_created.append(space)

    # Distribution elements with defects
    elem_types = [
        ("IfcBoiler", "IfcBoilerType", "Remeha", "Ss_25", "Heating"),
        ("IfcFan", "IfcFanType", "FläktGroup", "Ss_30", "Ventilation"),
        ("IfcPump", "IfcPumpType", "Grundfos", "Ss_40", "Water"),
    ]
    for i, (etype, ttype, mfg, class_id, system_name) in enumerate(elem_types):
        elem = f.create_entity(etype, GlobalId=ifcopenshell.guid.new(), Name=f"{mfg}_{i + 1}")
        # Defect: some without type
        if i % 2 == 0:
            type_ent = f.create_entity(ttype, GlobalId=ifcopenshell.guid.new(), Name=mfg)
            f.create_entity(
                "IfcRelDefinesByType", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[elem], RelatingType=type_ent
            )
        # Defect: some without classification
        if i % 3 != 0:
            class_ref = f.create_entity("IfcClassificationReference", Identification=class_id, Name=system_name)
            f.create_entity(
                "IfcRelAssociatesClassification",
                GlobalId=ifcopenshell.guid.new(),
                RelatedObjects=[elem],
                RelatingClassification=class_ref,
            )
        # Defect: some without space containment
        if i % 4 != 0 and spaces_created:
            f.create_entity(
                "IfcRelContainedInSpatialStructure",
                GlobalId=ifcopenshell.guid.new(),
                RelatedElements=[elem],
                RelatingStructure=spaces_created[0],
            )
        # System membership
        system = f.create_entity("IfcSystem", GlobalId=ifcopenshell.guid.new(), Name=system_name)
        f.create_entity(
            "IfcRelAssignsToGroup", GlobalId=ifcopenshell.guid.new(), RelatedObjects=[elem], RelatingGroup=system
        )

    # Duplicate names
    for i in range(2):
        f.create_entity("IfcBoiler", GlobalId=ifcopenshell.guid.new(), Name="DuplicateBoiler")

    # Zero-area space
    zero_space = f.create_entity("IfcSpace", GlobalId=ifcopenshell.guid.new(), Name="ZeroArea")
    qto_zero = f.create_entity("IfcElementQuantity", GlobalId=ifcopenshell.guid.new(), Name="Qto_SpaceBaseQuantities")
    area_zero = f.create_entity("IfcQuantityArea", Name="GrossFloorArea", AreaValue=0.0)
    qto_zero.Quantities = [area_zero]
    f.create_entity(
        "IfcRelDefinesByProperties",
        GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[zero_space],
        RelatingPropertyDefinition=qto_zero,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    f.write(str(out))
    print(f"Wrote {out} with {len(spaces_created)} spaces, {len(elem_types)} element types, planted defects")
    print(f"  Missing rooms: {missing_rooms}")
    print(f"  Area mismatch rooms: {mismatch_rooms}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/ifc/sample_b003.ifc"))
    parser.add_argument("--building", default="B003")
    args = parser.parse_args()
    make_sample_ifc(args.out, args.building)
