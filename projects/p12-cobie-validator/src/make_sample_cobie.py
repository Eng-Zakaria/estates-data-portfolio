"""Generate a valid COBie workbook for a campus building plus a corrupted variant.

Valid: all 19 sheets present, mandatory columns filled, keys consistent.
Corrupted: >=40 seeded errors across categories, logged to seeded_errors.json
(synthetic data for portfolio demonstration only).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

SHEETS = [
    "Contact",
    "Facility",
    "Floor",
    "Space",
    "Zone",
    "Type",
    "Component",
    "System",
    "Assembly",
    "Connection",
    "Spare",
    "Resource",
    "Job",
    "Impact",
    "Document",
    "Attribute",
    "Coordinate",
    "Issue",
    "Picture",
]

ADMIN = "admin@campus.ac.uk"
DATE = "2026-01-01"


def _contact_rows() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "CreatedOn": DATE,
                "CreatedBy": ADMIN,
                "Category": "Architect",
                "Email": ADMIN,
                "Phone": "+44 1392 123456",
                "Company": "Campus Estates",
                "Department": "Facilities",
                "OrganizationCode": "CAMP",
                "GivenName": "Alice",
                "FamilyName": "Admin",
            },
            {
                "CreatedOn": DATE,
                "CreatedBy": ADMIN,
                "Category": "Contractor",
                "Email": "contractor@example.co.uk",
                "Phone": "+44 1392 654321",
                "Company": "BIM Build Ltd",
                "Department": "Delivery",
                "OrganizationCode": "BIMB",
                "GivenName": "Bob",
                "FamilyName": "Builder",
            },
        ]
    )


def _valid_frames() -> dict[str, pd.DataFrame]:
    return {
        "Contact": _contact_rows(),
        "Facility": pd.DataFrame(
            [
                {
                    "Name": "Building C",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Educational",
                    "ProjectName": "Campus Estate",
                    "SiteName": "Streatham",
                    "LinearUnits": "meter",
                    "AreaUnits": "square meter",
                    "VolumeUnits": "cubic meter",
                    "CurrencyUnit": "GBP",
                    "AreaMeasurement": "Gross internal area",
                }
            ]
        ),
        "Floor": pd.DataFrame(
            [
                {
                    "Name": "L00",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Floor",
                    "FloorNumber": 0,
                    "Height": 3.5,
                },
                {
                    "Name": "L01",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Floor",
                    "FloorNumber": 1,
                    "Height": 3.5,
                },
                {
                    "Name": "L02",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Floor",
                    "FloorNumber": 2,
                    "Height": 3.2,
                },
            ]
        ),
        "Space": pd.DataFrame(
            [
                {
                    "Name": "B003-L00-001",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Office",
                    "FloorName": "L00",
                    "Description": "Office",
                    "RoomTag": "001",
                    "UsableHeight": 2.7,
                    "GrossArea": 50.0,
                    "NetArea": 45.0,
                },
                {
                    "Name": "B003-L00-002",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Store",
                    "FloorName": "L00",
                    "Description": "Store",
                    "RoomTag": "002",
                    "UsableHeight": 2.7,
                    "GrossArea": 20.0,
                    "NetArea": 18.0,
                },
                {
                    "Name": "B003-L01-001",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Teaching",
                    "FloorName": "L01",
                    "Description": "Lecture theatre",
                    "RoomTag": "101",
                    "UsableHeight": 4.0,
                    "GrossArea": 200.0,
                    "NetArea": 180.0,
                },
                {
                    "Name": "B003-L02-001",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Laboratory",
                    "FloorName": "L02",
                    "Description": "Lab",
                    "RoomTag": "201",
                    "UsableHeight": 3.0,
                    "GrossArea": 120.0,
                    "NetArea": 110.0,
                },
            ]
        ),
        "Zone": pd.DataFrame(
            [
                {
                    "Name": "Heating Zone L00",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Heating",
                    "SpaceNames": "B003-L00-001, B003-L00-002",
                },
            ]
        ),
        "Type": pd.DataFrame(
            [
                {
                    "Name": "BoilerType1",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Boiler",
                    "AssetType": "Fixed",
                    "Manufacturer": "Remeha",
                    "ModelNumber": "Quinta Pro",
                    "WarrantyDurationParts": 24,
                    "ExpectedLife": 15,
                },
                {
                    "Name": "AHUType1",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Air Handling Unit",
                    "AssetType": "Fixed",
                    "Manufacturer": "FlaktGroup",
                    "ModelNumber": "eQPrime",
                    "WarrantyDurationParts": 12,
                    "ExpectedLife": 20,
                },
                {
                    "Name": "FCUType1",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Fan Coil",
                    "AssetType": "Fixed",
                    "Manufacturer": "Daikin",
                    "ModelNumber": "FXDQ20",
                    "WarrantyDurationParts": 12,
                    "ExpectedLife": 15,
                },
                {
                    "Name": "PumpType1",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Pump",
                    "AssetType": "Fixed",
                    "Manufacturer": "Grundfos",
                    "ModelNumber": "MAGNA3",
                    "WarrantyDurationParts": 24,
                    "ExpectedLife": 12,
                },
                {
                    "Name": "LightType1",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Lighting",
                    "AssetType": "Fixed",
                    "Manufacturer": "Thorn",
                    "ModelNumber": "Omega",
                    "WarrantyDurationParts": 60,
                    "ExpectedLife": 10,
                },
            ]
        ),
        "Component": pd.DataFrame(
            [
                {
                    "Name": "Boiler-01",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Boiler",
                    "TypeName": "BoilerType1",
                    "Space": "B003-L00-001",
                    "Description": "Boiler 1",
                    "SerialNumber": "SN10001",
                    "InstallationDate": "2025-09-01",
                },
                {
                    "Name": "Boiler-02",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Boiler",
                    "TypeName": "BoilerType1",
                    "Space": "B003-L00-002",
                    "Description": "Boiler 2",
                    "SerialNumber": "SN10002",
                    "InstallationDate": "2025-09-02",
                },
                {
                    "Name": "AHU-01",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Air Handling Unit",
                    "TypeName": "AHUType1",
                    "Space": "B003-L01-001",
                    "Description": "AHU 1",
                    "SerialNumber": "SN10003",
                    "InstallationDate": "2025-08-15",
                },
                {
                    "Name": "AHU-02",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Air Handling Unit",
                    "TypeName": "AHUType1",
                    "Space": "B003-L02-001",
                    "Description": "AHU 2",
                    "SerialNumber": "SN10004",
                    "InstallationDate": "2025-08-16",
                },
                {
                    "Name": "FCU-01",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Fan Coil",
                    "TypeName": "FCUType1",
                    "Space": "B003-L01-001",
                    "Description": "FCU 1",
                    "SerialNumber": "SN10005",
                    "InstallationDate": "2025-08-20",
                },
                {
                    "Name": "FCU-02",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Fan Coil",
                    "TypeName": "FCUType1",
                    "Space": "B003-L02-001",
                    "Description": "FCU 2",
                    "SerialNumber": "SN10006",
                    "InstallationDate": "2025-08-21",
                },
                {
                    "Name": "Pump-01",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Pump",
                    "TypeName": "PumpType1",
                    "Space": "B003-L00-001",
                    "Description": "Pump 1",
                    "SerialNumber": "SN10007",
                    "InstallationDate": "2025-09-05",
                },
                {
                    "Name": "Light-01",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Lighting",
                    "TypeName": "LightType1",
                    "Space": "B003-L01-001",
                    "Description": "Light 1",
                    "SerialNumber": "SN10008",
                    "InstallationDate": "2025-09-06",
                },
            ]
        ),
        "System": pd.DataFrame(
            [
                {
                    "Name": "Heating-L00",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Heating",
                    "ComponentNames": "Boiler-01, Boiler-02, Pump-01",
                },
                {
                    "Name": "Vent-L01",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Ventilation",
                    "ComponentNames": "AHU-01, AHU-02",
                },
            ]
        ),
        "Assembly": pd.DataFrame(
            columns=["Name", "CreatedOn", "CreatedBy", "Category", "SheetName1", "ParentName", "ChildNames"]
        ),
        "Connection": pd.DataFrame(
            columns=["Name", "CreatedOn", "CreatedBy", "Category", "ConnectionType", "Row1", "Row2", "Port1", "Port2"]
        ),
        "Spare": pd.DataFrame(columns=["Name", "CreatedOn", "CreatedBy", "Category", "SetNumber", "PartName"]),
        "Resource": pd.DataFrame(columns=["Name", "CreatedOn", "CreatedBy", "Category", "ResourceType"]),
        "Job": pd.DataFrame(
            [
                {
                    "Name": "Job-Boiler-PPM",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Planned",
                    "TypeName": "BoilerType1",
                    "Frequency": "Monthly",
                    "TaskDuration": 2,
                    "DurationUnit": "hour",
                },
                {
                    "Name": "Job-AHU-PPM",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Planned",
                    "TypeName": "AHUType1",
                    "Frequency": "Quarterly",
                    "TaskDuration": 4,
                    "DurationUnit": "hour",
                },
            ]
        ),
        "Impact": pd.DataFrame(
            columns=[
                "Name",
                "CreatedOn",
                "CreatedBy",
                "Category",
                "ImpactStage",
                "ImpactType",
                "ImpactStageDuration",
                "ImpactCapabilities",
                "ImpactLocation",
            ]
        ),
        "Document": pd.DataFrame(
            [
                {
                    "Name": "O&M Boiler",
                    "CreatedOn": DATE,
                    "CreatedBy": ADMIN,
                    "Category": "Manual",
                    "SheetName": "Type",
                    "RowName1": "BoilerType1",
                    "File": "om_boiler.pdf",
                    "Description": "O&M manual",
                },
            ]
        ),
        "Attribute": pd.DataFrame(
            columns=[
                "SheetName",
                "RowName",
                "AttributeName",
                "AttributeCategory",
                "Value",
                "Unit",
                "CreatedOn",
                "CreatedBy",
            ]
        ),
        "Coordinate": pd.DataFrame(
            columns=[
                "Name",
                "Category",
                "SheetName",
                "RowName1",
                "RowName2",
                "RowName3",
                "CreatedOn",
                "CreatedBy",
                "CoordinateXAxis",
                "CoordinateYAxis",
                "CoordinateZAxis",
                "CoordinateSpace",
            ]
        ),
        "Issue": pd.DataFrame(
            columns=[
                "Name",
                "CreatedOn",
                "CreatedBy",
                "Category",
                "Owner",
                "OwnerRole",
                "IssuedDate",
                "Status",
                "Description",
            ]
        ),
        "Picture": pd.DataFrame(
            columns=[
                "Name",
                "CreatedOn",
                "CreatedBy",
                "Category",
                "RowName",
                "RowName1",
                "RowName2",
                "RowName3",
                "UploadDate",
                "DocumentName",
                "Description",
            ]
        ),
    }


def write_workbook(dfs: dict[str, pd.DataFrame], out: Path, only_keys: bool = False) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    sheets = list(dfs.keys()) if only_keys else SHEETS
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet in sheets:
            df = dfs.get(sheet, pd.DataFrame())
            df.to_excel(writer, sheet_name=sheet, index=False)


def make_valid_cobie(out: Path) -> None:
    write_workbook(_valid_frames(), out)
    print(f"Valid COBie written to {out}")


def make_corrupted_cobie(out: Path) -> list[dict]:
    """Build corrupted variant; return seeded error log (each a dict with category/rule)."""
    dfs = _valid_frames()
    seeded: list[dict] = []

    def log(category: str, rule: str, detail: str) -> None:
        seeded.append({"category": category, "expected_rule": rule, "detail": detail})

    # 1-2. Missing sheets: Zone, Document
    for sheet in ("Zone", "Document"):
        del dfs[sheet]
        log("missing_sheet", "sheet_present", f" dropped sheet {sheet}")

    # 3-4. Missing columns: Contact.Phone, Type.ModelNumber
    dfs["Contact"] = dfs["Contact"].drop(columns=["Phone"])
    log("missing_column", "column_present", "Contact.Phone dropped")
    dfs["Type"] = dfs["Type"].drop(columns=["ModelNumber"])
    log("missing_column", "column_present", "Type.ModelNumber dropped")

    # 5. Column order: swap Component Name/TypeName
    cols = list(dfs["Component"].columns)
    i1, i2 = cols.index("Name"), cols.index("TypeName")
    cols[i1], cols[i2] = cols[i2], cols[i1]
    dfs["Component"] = dfs["Component"][cols]
    log("column_order", "column_order", "Component Name/TypeName swapped")

    # 6-11. Empty mandatory cells (6 events)
    dfs["Facility"].loc[0, "CreatedOn"] = None
    log("empty_mandatory", "mandatory_not_empty", "Facility.CreatedOn blank")
    dfs["Space"].loc[0, "FloorName"] = ""
    log("empty_mandatory", "mandatory_not_empty", "Space[0].FloorName blank")
    dfs["Space"].loc[2, "FloorName"] = None
    log("empty_mandatory", "mandatory_not_empty", "Space[2].FloorName blank")
    dfs["Component"].loc[0, "TypeName"] = ""
    log("empty_mandatory", "mandatory_not_empty", "Component[0].TypeName blank")
    dfs["Floor"].loc[1, "Name"] = None
    log("empty_mandatory", "mandatory_not_empty", "Floor[1].Name blank")
    dfs["Type"].loc[1, "Name"] = ""
    log("empty_mandatory", "mandatory_not_empty", "Type[1].Name blank")

    # 12-14. Duplicate keys (3 events -> multiple row issues)
    dfs["Component"] = pd.concat([dfs["Component"], dfs["Component"].iloc[[0]]], ignore_index=True)
    log("duplicate_key", "unique_key", "Component.Name Boiler-01 duplicated")
    dfs["Type"] = pd.concat([dfs["Type"], dfs["Type"].iloc[[2]]], ignore_index=True)
    log("duplicate_key", "unique_key", "Type.Name FCUType1 duplicated")
    dfs["Space"] = pd.concat([dfs["Space"], dfs["Space"].iloc[[1]]], ignore_index=True)
    log("duplicate_key", "unique_key", "Space.Name B003-L00-002 duplicated")

    # 15-23. Broken FKs (9 events)
    dfs["Component"].loc[1, "TypeName"] = "UnknownType"
    log("broken_fk", "fk", "Component[1].TypeName=UnknownType")
    dfs["Component"].loc[2, "TypeName"] = "GhostType"
    log("broken_fk", "fk", "Component[2].TypeName=GhostType")
    dfs["Component"].loc[3, "Space"] = "NoSuchSpace"
    log("broken_fk", "fk", "Component[3].Space=NoSuchSpace")
    dfs["Component"].loc[4, "Space"] = "B003-L00-001; GhostSpace"
    log("broken_fk_multivalue", "fk", "Component[4].Space multi-value with GhostSpace")
    dfs["Space"].loc[3, "FloorName"] = "NoSuchFloor"
    log("broken_fk", "fk", "Space[3].FloorName=NoSuchFloor")
    dfs["System"].loc[0, "ComponentNames"] = "Boiler-01, Ghost-99"
    log("broken_fk_multivalue", "fk", "System[0].ComponentNames includes Ghost-99")
    dfs["Job"].loc[0, "TypeName"] = "GhostType"
    log("broken_fk", "fk", "Job[0].TypeName=GhostType")
    dfs["Component"].loc[5, "CreatedBy"] = "ghost@nowhere.ac.uk"
    log("broken_fk_createdby", "created_by", "Component[5].CreatedBy ghost")
    dfs["Space"].loc[0, "CreatedBy"] = "ghost@nowhere.ac.uk"
    log("broken_fk_createdby", "created_by", "Space[0].CreatedBy ghost")

    # 24. Bad email format (contractor row; admin kept valid so CreatedBy still resolves)
    dfs["Contact"].loc[1, "Email"] = "not-an-email"
    log("bad_format_email", "format", "Contact[1].Email not-an-email")

    # 25-27. Bad date formats (3 events)
    dfs["Component"].loc[0, "InstallationDate"] = "32/13/2025"
    log("bad_format_date", "format", "Component[0].InstallationDate 32/13/2025")
    dfs["Component"].loc[1, "InstallationDate"] = "01/02/2026"
    log("bad_format_date", "format", "Component[1].InstallationDate 01/02/2026")
    dfs["Type"].loc[0, "CreatedOn"] = "01-02-2026"
    log("bad_format_date", "format", "Type[0].CreatedOn 01-02-2026")

    # 28-31. Numeric range violations (4 events)
    dfs["Space"].loc[1, "GrossArea"] = -5.0
    log("numeric_range", "numeric_range", "Space[1].GrossArea=-5")
    dfs["Floor"].loc[0, "Height"] = 99.0
    log("numeric_range", "numeric_range", "Floor[0].Height=99")
    dfs["Type"].loc[2, "ExpectedLife"] = 999
    log("numeric_range", "numeric_range", "Type[2].ExpectedLife=999")
    dfs["Type"].loc[3, "WarrantyDurationParts"] = -3
    log("numeric_range", "numeric_range", "Type[3].Warranty=-3")

    # 32-34. Invalid categories (3 events)
    dfs["Type"].loc[0, "Category"] = "???"
    log("invalid_category", "category_pattern", "Type[0].Category=???")
    dfs["Type"].loc[3, "Category"] = "!!!"
    log("invalid_category", "category_pattern", "Type[3].Category=!!!")
    dfs["Component"].loc[6, "Category"] = "???"
    log("invalid_category", "category_pattern", "Component[6].Category=???")

    # 35-41. Missing AIR attributes (7 events)
    dfs["Type"].loc[0, "Manufacturer"] = None
    log("missing_air", "required_attribute", "Type[0].Manufacturer blank")
    dfs["Type"].loc[4, "Manufacturer"] = ""
    log("missing_air", "required_attribute", "Type[4].Manufacturer blank")
    dfs["Type"].loc[1, "ExpectedLife"] = None
    log("missing_air", "required_attribute", "Type[1].ExpectedLife blank")
    dfs["Type"].loc[2, "WarrantyDurationParts"] = None
    log("missing_air", "required_attribute", "Type[2].Warranty blank")
    dfs["Type"].loc[4, "WarrantyDurationParts"] = None
    log("missing_air", "required_attribute", "Type[4].Warranty blank")
    dfs["Component"].loc[7, "SerialNumber"] = None
    log("missing_air", "required_attribute", "Component[7].SerialNumber blank")
    dfs["Component"].loc[6, "InstallationDate"] = ""
    log("missing_air", "required_attribute", "Component[6].InstallationDate blank")

    # 42. Duplicate serials (1 event -> 3 rows flagged)
    dfs["Component"].loc[1, "SerialNumber"] = "SN-DUP"
    dfs["Component"].loc[2, "SerialNumber"] = "SN-DUP"
    dfs["Component"].loc[3, "SerialNumber"] = "SN-DUP"
    log("duplicate_serial", "unique_key", "SerialNumber SN-DUP x3")

    write_workbook(dfs, out, only_keys=True)
    log_path = out.parent / "seeded_errors.json"
    log_path.write_text(json.dumps(seeded, indent=2), encoding="utf-8")
    print(f"Corrupted COBie written to {out} with {len(seeded)} seeded events")
    for e in seeded:
        print(f"  {e['category']}:{e['detail']}")
    return seeded


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--valid", type=Path, default=Path("data/cobie/valid.xlsx"))
    parser.add_argument("--corrupted", type=Path, default=Path("data/cobie/corrupted.xlsx"))
    args = parser.parse_args()
    make_valid_cobie(args.valid)
    make_corrupted_cobie(args.corrupted)
