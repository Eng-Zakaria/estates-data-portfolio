"""Extract analytical tables from an IFC file.

Tables: ifc_project, ifc_storeys, ifc_spaces, ifc_elements, ifc_types,
ifc_systems, ifc_system_members, ifc_properties_long, ifc_quantities_long,
ifc_classifications.

Stable key = IFC GlobalId. Area from Qto where present, fallback documented.
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path

import ifcopenshell
import pandas as pd


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()[:16]


def extract_tables(ifc_path: Path) -> dict[str, pd.DataFrame]:
    f = ifcopenshell.open(str(ifc_path))
    t0 = time.time()

    # Project
    projects = f.by_type("IfcProject")
    df_project = pd.DataFrame(
        [
            {
                "global_id": p.GlobalId,
                "name": p.Name,
                "schema": f.schema,
            }
            for p in projects
        ]
    )

    # Storeys
    storeys = f.by_type("IfcBuildingStorey")
    df_storeys = pd.DataFrame(
        [
            {
                "global_id": s.GlobalId,
                "name": s.Name,
            }
            for s in storeys
        ]
    )

    # Spaces
    spaces = f.by_type("IfcSpace")
    space_rows = []
    for s in spaces:
        area_val = None
        area_source = None
        for rel in f.by_type("IfcRelDefinesByProperties"):
            if s in rel.RelatedObjects:
                defn = rel.RelatingPropertyDefinition
                if defn and defn.is_a("IfcElementQuantity") and defn.Name == "Qto_SpaceBaseQuantities":
                    for q in defn.Quantities or []:
                        if q.Name == "GrossFloorArea":
                            area_val = q.AreaValue
                            area_source = "Qto"
        space_rows.append(
            {
                "global_id": s.GlobalId,
                "name": s.Name,
                "area_m2": area_val,
                "area_source": area_source,
            }
        )
    df_spaces = pd.DataFrame(space_rows)

    # Elements
    elements = f.by_type("IfcElement")
    elem_rows = []
    for e in elements:
        elem_rows.append(
            {
                "global_id": e.GlobalId,
                "name": e.Name,
                "ifc_class": e.is_a(),
            }
        )
    df_elements = pd.DataFrame(elem_rows)

    # Types
    types = f.by_type("IfcTypeObject")
    type_rows = []
    for t in types:
        type_rows.append(
            {
                "global_id": t.GlobalId,
                "name": t.Name,
                "ifc_class": t.is_a(),
            }
        )
    df_types = pd.DataFrame(type_rows)

    # Systems
    systems = f.by_type("IfcSystem")
    system_rows = []
    for s in systems:
        system_rows.append(
            {
                "global_id": s.GlobalId,
                "name": s.Name,
            }
        )
    df_systems = pd.DataFrame(system_rows)

    # System members
    member_rows = []
    for rel in f.by_type("IfcRelAssignsToGroup"):
        if rel.RelatingGroup:
            for obj in rel.RelatedObjects or []:
                member_rows.append(
                    {
                        "system_global_id": rel.RelatingGroup.GlobalId,
                        "element_global_id": obj.GlobalId,
                    }
                )
    df_system_members = pd.DataFrame(member_rows)

    # Properties long
    prop_rows = []
    for rel in f.by_type("IfcRelDefinesByProperties"):
        defn = rel.RelatingPropertyDefinition
        if defn and defn.is_a("IfcPropertySet"):
            for p in defn.HasProperties or []:
                if hasattr(p, "NominalValue") and p.NominalValue:
                    val = getattr(p.NominalValue, "wrappedValue", str(p.NominalValue))
                else:
                    val = None
                for rel_obj in rel.RelatedObjects or []:
                    prop_rows.append(
                        {
                            "global_id": rel_obj.GlobalId,
                            "pset": defn.Name,
                            "property": p.Name,
                            "value": val,
                            "unit": None,
                        }
                    )
    df_properties = pd.DataFrame(prop_rows)

    # Quantities long
    qty_rows = []
    for rel in f.by_type("IfcRelDefinesByProperties"):
        defn = rel.RelatingPropertyDefinition
        if defn and defn.is_a("IfcElementQuantity"):
            for q in defn.Quantities or []:
                val = getattr(q, "AreaValue", getattr(q, "LengthValue", getattr(q, "VolumeValue", None)))
                for rel_obj in rel.RelatedObjects or []:
                    qty_rows.append(
                        {
                            "global_id": rel_obj.GlobalId,
                            "qto": defn.Name,
                            "quantity": q.Name,
                            "value": val,
                            "unit": "m2" if "Area" in q.is_a() else None,
                        }
                    )
    df_quantities = pd.DataFrame(qty_rows)

    # Classifications
    class_rows = []
    for rel in f.by_type("IfcRelAssociatesClassification"):
        cref = rel.RelatingClassification
        if cref:
            for obj in rel.RelatedObjects or []:
                class_rows.append(
                    {
                        "global_id": obj.GlobalId,
                        "classification_id": getattr(cref, "Identification", None),
                        "classification_name": getattr(cref, "Name", None),
                    }
                )
    df_classifications = pd.DataFrame(class_rows)

    elapsed = time.time() - t0
    print(f"Extracted {len(df_spaces)} spaces, {len(df_elements)} elements,")
    print(f"  {len(df_types)} types, {len(df_systems)} systems in {elapsed:.2f}s")

    return {
        "ifc_project": df_project,
        "ifc_storeys": df_storeys,
        "ifc_spaces": df_spaces,
        "ifc_elements": df_elements,
        "ifc_types": df_types,
        "ifc_systems": df_systems,
        "ifc_system_members": df_system_members,
        "ifc_properties_long": df_properties,
        "ifc_quantities_long": df_quantities,
        "ifc_classifications": df_classifications,
    }


def write_tables(tables: dict[str, pd.DataFrame], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(out_dir / f"{name}.parquet", index=False)
    print(f"Wrote {len(tables)} tables to {out_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("ifc", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/gold/ifc"))
    args = parser.parse_args()
    tables = extract_tables(args.ifc)
    write_tables(tables, args.out)
