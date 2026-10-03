"""Pydantic v2 schemas for every truth table (used by tests + contracts)."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field

SpaceCategory = Literal["Teaching", "Office", "Laboratory", "Library", "Residential", "Catering", "Sports", "Support"]
ConditionGrade = Literal["A", "B", "C", "D"]
WoType = Literal["PPM", "Reactive", "Statutory", "Project"]
Priority = Literal["P1", "P2", "P3", "P4"]
Utility = Literal["electricity", "gas", "water", "heat"]


class Building(BaseModel):
    building_id: str = Field(pattern=r"^B\d{3}$")
    building_name: str
    campus: str
    gia_m2: float = Field(gt=0)
    nia_m2: float = Field(gt=0)
    n_floors: int = Field(ge=1, le=12)
    year_built: int = Field(ge=1800, le=2026)
    primary_use: str
    heating_fuel: str
    epc_band: str = Field(pattern=r"^[A-G]$")
    lat: float
    lon: float
    ifc_available: bool


class Floor(BaseModel):
    floor_id: str
    building_id: str = Field(pattern=r"^B\d{3}$")
    level_code: str
    level_name: str


class Department(BaseModel):
    department_id: str
    name: str
    faculty: str
    staff_fte: float = Field(ge=0)
    student_fte: float = Field(ge=0)


class Space(BaseModel):
    space_id: str
    building_id: str
    floor_id: str
    room_code: str
    space_category: SpaceCategory
    space_type: str
    capacity_seats: int = Field(ge=0)
    nia_m2: float = Field(gt=0, lt=2000)
    department_id: str
    ifc_guid: str | None = None
    valid_from: date
    valid_to: date | None = None


class Asset(BaseModel):
    asset_id: str
    building_id: str
    space_id: str
    asset_type: str
    description_raw: str
    manufacturer: str
    model: str
    serial_no: str
    install_date: date
    expected_life_years: int = Field(ge=1, le=60)
    condition_grade: ConditionGrade
    criticality: int = Field(ge=1, le=5)
    replacement_cost_gbp: float = Field(ge=0)
    cobie_type: str
    uniclass_code_true: str | None = None
    ifc_guid: str | None = None


class WorkOrder(BaseModel):
    wo_id: str
    asset_id: str
    space_id: str
    building_id: str
    wo_type: WoType
    priority: Priority
    raised_ts: datetime
    target_ts: datetime
    started_ts: datetime | None = None
    completed_ts: datetime | None = None
    status: str
    trade: str
    contractor: str
    labour_hours: float = Field(ge=0)
    cost_gbp: float = Field(ge=0)
    fault_code: str
    description: str


class Meter(BaseModel):
    meter_id: str
    building_id: str
    utility: Utility
    meter_role: Literal["main", "sub"]
    parent_meter_id: str | None = None
    unit: str
    interval: str
    mpan_mprn_synthetic: str


TABLE_SCHEMAS: dict[str, type[BaseModel]] = {
    "buildings": Building,
    "floors": Floor,
    "departments": Department,
    "spaces": Space,
    "assets": Asset,
    "work_orders": WorkOrder,
    "meters": Meter,
}
