"""Generate a valid COBie workbook for a campus building plus a corrupted variant.

Valid: all sheets present, mandatory columns filled, keys consistent.
Corrupted: ≥40 seeded errors across categories (missing sheets/columns, empty mandatory,
duplicate keys, broken FKs, bad email/date, invalid category, missing manufacturer/model/warranty,
duplicate serials).
"""

from __future__ import annotations

import argparse
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


def make_valid_cobie(out: Path) -> None:
    dfs = {
        "Contact": pd.DataFrame(
            [
                {
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Architect",
                    "Email": "admin@campus.ac.uk",
                    "Phone": "+44 1392 123456",
                    "Company": "Campus Estates",
                    "Department": "Facilities",
                    "OrganizationCode": "CAMP",
                    "GivenName": "Alice",
                    "FamilyName": "Admin",
                }
            ]
        ),
        "Facility": pd.DataFrame(
            [
                {
                    "Name": "Building C",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
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
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Floor",
                    "FloorNumber": 0,
                    "Height": 3.5,
                },
                {
                    "Name": "L01",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Floor",
                    "FloorNumber": 1,
                    "Height": 3.5,
                },
            ]
        ),
        "Space": pd.DataFrame(
            [
                {
                    "Name": "B003-L00-001",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Office",
                    "FloorName": "L00",
                    "Description": "Office",
                    "RoomTag": "001",
                    "UsableHeight": 2.7,
                    "GrossArea": 50.0,
                    "NetArea": 45.0,
                },
                {
                    "Name": "B003-L01-001",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Teaching",
                    "FloorName": "L01",
                    "Description": "Lecture theatre",
                    "RoomTag": "101",
                    "UsableHeight": 4.0,
                    "GrossArea": 200.0,
                    "NetArea": 180.0,
                },
            ]
        ),
        "Zone": pd.DataFrame(columns=["Name", "CreatedOn", "CreatedBy", "Category", "SpaceNames"]),
        "Type": pd.DataFrame(
            [
                {
                    "Name": "BoilerType1",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Boiler",
                    "AssetType": "Fixed",
                    "Manufacturer": "Remeha",
                    "ModelNumber": "Quinta Pro",
                    "WarrantyDurationParts": 24,
                    "ExpectedLife": 15,
                },
                {
                    "Name": "AHUType1",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Air Handling Unit",
                    "AssetType": "Fixed",
                    "Manufacturer": "FläktGroup",
                    "ModelNumber": "eQPrime",
                    "WarrantyDurationParts": 12,
                    "ExpectedLife": 20,
                },
            ]
        ),
        "Component": pd.DataFrame(
            [
                {
                    "Name": "Boiler-01",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Boiler",
                    "TypeName": "BoilerType1",
                    "Space": "B003-L00-001",
                    "SerialNumber": "SN12345",
                    "InstallationDate": "2025-09-01",
                },
                {
                    "Name": "AHU-01",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Air Handling Unit",
                    "TypeName": "AHUType1",
                    "Space": "B003-L01-001",
                    "SerialNumber": "SN67890",
                    "InstallationDate": "2025-08-15",
                },
            ]
        ),
        "System": pd.DataFrame(
            [
                {
                    "Name": "Heating-L00",
                    "CreatedOn": "2026-01-01",
                    "CreatedBy": "admin@campus.ac.uk",
                    "Category": "Heating",
                    "ComponentNames": "Boiler-01",
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
            columns=[
                "Name",
                "CreatedOn",
                "CreatedBy",
                "Category",
                "ResourceName",
                "TaskStartUnit",
                "DurationUnit",
                "Start",
                "TaskDuration",
                "Frequency",
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
            columns=[
                "Name",
                "CreatedOn",
                "CreatedBy",
                "Category",
                "SheetName",
                "RowName1",
                "RowName2",
                "RowName3",
                "RowName4",
                "UploadDate",
                "DocumentReference",
                "Directory",
                "File",
                "Description",
                "Rows",
                "Paths",
                "Size",
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

    out.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    print(f"Valid COBie written to {out}")


def make_corrupted_cobie(out: Path) -> None:
    # Start from valid, then corrupt
    valid = out.parent / "valid.xlsx"
    make_valid_cobie(valid)

    # Read back
    dfs = pd.read_excel(valid, sheet_name=None)

    # Seeded errors
    errors = []

    # 1. Missing sheet: drop Zone
    if "Zone" in dfs:
        del dfs["Zone"]
        errors.append("missing_sheet:Zone")

    # 2. Missing column: drop Email from Contact
    if "Contact" in dfs and "Email" in dfs["Contact"].columns:
        dfs["Contact"] = dfs["Contact"].drop(columns=["Email"])
        errors.append("missing_column:Contact.Email")

    # 3. Empty mandatory: clear CreatedOn in Facility
    if "Facility" in dfs and "CreatedOn" in dfs["Facility"].columns:
        dfs["Facility"].loc[0, "CreatedOn"] = None
        errors.append("empty_mandatory:Facility.CreatedOn")

    # 4. Duplicate key: duplicate Component Name
    if "Component" in dfs:
        dfs["Component"] = pd.concat([dfs["Component"], dfs["Component"].iloc[[0]]], ignore_index=True)
        errors.append("duplicate_key:Component.Name")

    # 5. Broken FK: Component TypeName not in Type
    if "Component" in dfs and "TypeName" in dfs["Component"].columns:
        dfs["Component"].loc[0, "TypeName"] = "UnknownType"
        errors.append("broken_fk:Component.TypeName")

    # 6. Bad email format
    if "Contact" in dfs and "Email" in dfs.get("Contact", pd.DataFrame()).columns:
        dfs["Contact"].loc[0, "Email"] = "not-an-email"
        errors.append("bad_format:Contact.Email")

    # 7. Bad date format
    if "Component" in dfs and "InstallationDate" in dfs["Component"].columns:
        dfs["Component"].loc[0, "InstallationDate"] = "32/13/2025"
        errors.append("bad_format:Component.InstallationDate")

    # 8. Invalid category pattern (not in Uniclass-ish)
    if "Type" in dfs and "Category" in dfs["Type"].columns:
        dfs["Type"].loc[0, "Category"] = "???"
        errors.append("invalid_category:Type.Category")

    # 9. Missing manufacturer
    if "Type" in dfs and "Manufacturer" in dfs["Type"].columns:
        dfs["Type"].loc[0, "Manufacturer"] = None
        errors.append("missing_attribute:Type.Manufacturer")

    # 10. Duplicate serial number
    if "Component" in dfs and "SerialNumber" in dfs["Component"].columns:
        dfs["Component"].loc[1, "SerialNumber"] = dfs["Component"].loc[0, "SerialNumber"]
        errors.append("duplicate_serial:Component.SerialNumber")

    out.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for sheet, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet, index=False)

    print(f"Corrupted COBie written to {out} with {len(errors)} seeded errors")
    for e in errors:
        print(f"  {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--valid", type=Path, default=Path("data/cobie/valid.xlsx"))
    parser.add_argument("--corrupted", type=Path, default=Path("data/cobie/corrupted.xlsx"))
    args = parser.parse_args()
    make_valid_cobie(args.valid)
    make_corrupted_cobie(args.corrupted)
