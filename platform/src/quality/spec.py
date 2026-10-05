"""P03 check specifications: pydantic models, YAML loading, dataset registry.

Every check is declared in ``platform/quality/checks/*.yml`` with: id, dataset,
dimension, severity, threshold (min pass %), owner, description, why_it_matters,
plus engine-specific config (``engine: gx`` with expectation+kwargs, or
``engine: sql`` / ``engine: recall`` with queries/rules). Threshold maps to GX
``mostly = threshold / 100``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator

Dimension = Literal[
    "completeness",
    "uniqueness",
    "validity",
    "consistency",
    "timeliness",
    "referential_integrity",
    "reconciliation",
]
Severity = Literal["error", "warn", "info"]
Engine = Literal["gx", "sql", "recall"]

SEVERITY_WEIGHTS: dict[str, float] = {"error": 3.0, "warn": 2.0, "info": 1.0}

GX_EXPECTATIONS: dict[str, set[str]] = {
    # expectation name -> allowed kwarg keys (subset of the real GX signature,
    # just what the compiler supports; anything else is a spec error).
    "ExpectColumnValuesToNotBeNull": {"column"},
    "ExpectColumnValuesToBeUnique": {"column"},
    "ExpectCompoundColumnsToBeUnique": {"column_list"},
    "ExpectColumnValuesToBeInSet": {"column", "value_set", "value_set_from"},
    "ExpectColumnValuesToBeBetween": {
        "column",
        "min_value",
        "max_value",
        "strict_min",
        "strict_max",
    },
    "ExpectColumnValuesToMatchRegex": {"column", "regex"},
    "ExpectTableRowCountToBeBetween": {"min_value", "max_value"},
}


class CheckSpec(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    dataset: str
    dimension: Dimension
    severity: Severity
    threshold: float = Field(ge=0.0, le=100.0)
    owner: str
    description: str
    why_it_matters: str
    engine: Engine
    expectation: str | None = None
    kwargs: dict[str, Any] | None = None
    sql_checked: str | None = None
    sql_failed: str | None = None
    failed_is_scalar: bool = False
    building_col: str | None = None
    by_building: bool = False
    sql_checked_by_building: str | None = None

    @field_validator("expectation")
    @classmethod
    def _expectation_known(cls, v: str | None) -> str | None:
        if v is not None and v not in GX_EXPECTATIONS:
            raise ValueError(f"unsupported GX expectation: {v}")
        return v

    def model_post_init(self, __context: Any) -> None:
        if self.engine == "gx":
            if not self.expectation or not self.kwargs:
                raise ValueError(f"gx check {self.id} needs expectation + kwargs")
            allowed = GX_EXPECTATIONS[self.expectation]
            unknown = set(self.kwargs) - allowed
            if unknown:
                raise ValueError(f"gx check {self.id}: unknown kwargs {unknown}")
        if self.engine == "sql":
            if not self.sql_checked or not self.sql_failed:
                raise ValueError(f"sql check {self.id} needs sql_checked + sql_failed")
        if self.by_building and not self.building_col:
            raise ValueError(f"check {self.id}: by_building needs building_col")
        if self.by_building and not self.sql_checked_by_building:
            raise ValueError(f"check {self.id}: by_building needs sql_checked_by_building")

    @property
    def mostly(self) -> float:
        """GX ``mostly`` fraction equivalent of the pass-% threshold."""
        return self.threshold / 100.0

    @property
    def weight(self) -> float:
        return SEVERITY_WEIGHTS[self.severity]


# Dataset -> inputs. Paths use run-time placeholders; truth tables are
# campus_synth reference data (synthetic); quarantine holds P01 rejects.
DATASETS: dict[str, dict[str, str]] = {
    "spaces": {
        "silver": "{lake}/silver/space_register/silver.parquet",
        "quarantine": "{lake}/quarantine/space_register/quarantine.parquet",
        "key": "room_code",
    },
    "assets": {
        "silver": "{truth}/assets.parquet",
        "key": "asset_id",
        "note": "no source register ingested in P01; checks run on truth reference",
    },
    "work_orders": {
        "silver": "{lake}/silver/cafm_workorders/silver.parquet",
        "quarantine": "{lake}/quarantine/cafm_workorders/quarantine.parquet",
        "key": "WO_Number",
    },
    "meters_a": {
        "silver": "{lake}/silver/meter_hh_supplierA/silver.parquet",
        "quarantine": "{lake}/quarantine/meter_hh_supplierA/quarantine.parquet",
        "key": "meter_id",
    },
    "meters_b": {
        "silver": "{lake}/silver/meter_hh_supplierB/silver.parquet",
        "quarantine": "{lake}/quarantine/meter_hh_supplierB/quarantine.parquet",
        "key": "meter_id",
    },
    "sensors": {
        "silver": "{lake}/silver/sensors/silver.parquet",
        "quarantine": "{lake}/quarantine/sensors/quarantine.parquet",
        "key": "sensor_id",
    },
    "bms": {
        "silver": "{lake}/silver/bms_trends/silver.parquet",
        "quarantine": "{lake}/quarantine/bms_trends/quarantine.parquet",
        "key": "point_id",
    },
    "inspections": {
        "silver": "{lake}/silver/statutory_inspections/silver.parquet",
        "quarantine": "{lake}/quarantine/statutory_inspections/quarantine.parquet",
        "key": "inspection_id",
    },
    "timetable": {
        "silver": "{lake}/silver/timetable/silver.parquet",
        "quarantine": "{lake}/quarantine/timetable/quarantine.parquet",
        "key": "event_id",
    },
    "spaces_snapshot": {
        "silver": "{snap}/spaces.parquet",
        "key": "space_id",
        "note": "weekly generator snapshots (spaces only) for trend scoring",
    },
}


def load_checks(checks_dir: str | Path) -> list[CheckSpec]:
    """Load and validate every ``*.yml`` check file (sorted for determinism)."""
    specs: list[CheckSpec] = []
    for path in sorted(Path(checks_dir).glob("*.yml")):
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        for raw in doc.get("checks", []):
            specs.append(CheckSpec(**raw))
    ids = [s.id for s in specs]
    if len(set(ids)) != len(ids):
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        raise ValueError(f"duplicate check ids: {dupes}")
    return specs
