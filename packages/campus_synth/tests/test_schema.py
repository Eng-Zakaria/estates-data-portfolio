"""Pydantic schema validation for truth tables."""

import pandas as pd
import pytest
from campus_synth.schemas import TABLE_SCHEMAS
from pydantic import ValidationError


def _validate(df: pd.DataFrame, model) -> None:
    for _, row in df.head(200).iterrows():
        d = row.to_dict()
        # normalise NaN/NaT -> None, datetimes stay
        for k, v in list(d.items()):
            if pd.isna(v):
                d[k] = None
        model(**d)


def test_schemas_pass_on_truth(small_truth):
    tables, _ = small_truth
    for name, model in TABLE_SCHEMAS.items():
        _validate(tables[name], model)


def test_schema_rejects_bad_building():
    from campus_synth.schemas import Building

    with pytest.raises(ValidationError):
        Building(
            building_id="X1",
            building_name="x",
            campus="North",
            gia_m2=-5,
            nia_m2=10,
            n_floors=2,
            year_built=2000,
            primary_use="Office",
            heating_fuel="gas",
            epc_band="Z",
            lat=0.0,
            lon=0.0,
            ifc_available=True,
        )
