"""Shared test setup: put the project's src on the path and expose handy paths."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_DIR / "src"))

import config  # noqa: E402


@pytest.fixture
def project_dir() -> Path:
    return PROJECT_DIR


@pytest.fixture
def registry():
    import metrics

    return metrics.load_registry(config.METRICS_YML)


@pytest.fixture
def glossary():
    import glossary as glossary_mod

    return glossary_mod.load_glossary(config.GLOSSARY_YML)


@pytest.fixture
def dax_fixture() -> str:
    """A hand-written DAX sample covering every case the extractor must handle."""
    return (
        "// P07 measures.dax - Asset & maintenance performance (synthetic).\n"
        "// Format strings included. Ties to validation/v01-v05.sql.\n"
        "\n"
        "// ---- Page 1: Overview ----\n"
        "\n"
        "// Total work orders raised. Format: 0\n"
        "Total WOs = COUNTROWS ( fct_work_order )\n"
        "\n"
        "// PPM completion % = PPM complete / PPM raised. Format: 0.0%\n"
        "PPM Completion % =\n"
        "DIVIDE (\n"
        '    CALCULATE ( COUNTROWS ( fct_work_order ), fct_work_order[wo_type] = "PPM" ),\n'
        '    CALCULATE ( COUNTROWS ( fct_work_order ), fct_work_order[status] = "Complete" )\n'
        ")\n"
        "\n"
        "// Remaining life % (asset grain). Format: 0%\n"
        "Remaining Life % = AVERAGE ( mart_asset_health[remaining_life_pct] )\n"
        "\n"
        "[Frequency %] =\n"
        "DIVIDE ( [Booked], [Possible] )\n"
        "\n"
        "// SLA met % by priority. Format: 0.0%\n"
        "SLA Met % =\n"
        "VAR TargetDays =\n"
        "    SWITCH (\n"
        "        SELECTEDVALUE ( fct_work_order[priority] ),\n"
        '        "P1", 1, "P2", 5,\n'
        "        BLANK ( )\n"
        "    )\n"
        "RETURN\n"
        "    DIVIDE ( 1, 2 )\n"
        "\n"
        "// Backlog age band (calculated column on fct_work_order, see build-guide):\n"
        "// 0-30 / 31-90 / 91-180 / 180+ days from raised_ts to as-of date.\n"
    )


@pytest.fixture
def dbt_fixture_tree(tmp_path: Path) -> Path:
    """A miniature dbt project: one YAML per layer, one SQL per model."""
    models = tmp_path / "models"
    (models / "staging").mkdir(parents=True)
    (models / "marts").mkdir(parents=True)

    (models / "staging.yml").write_text(
        "version: 2\n"
        "models:\n"
        "  - name: stg_meter__hh\n"
        "    description: Half-hourly readings as received.\n"
        "    columns:\n"
        "      - {name: meter_id, data_type: varchar, description: Meter id, tests: [not_null]}\n"
        "      - {name: kwh, data_type: double, description: kWh}\n",
        encoding="utf-8",
    )
    (models / "marts.yml").write_text(
        "version: 2\n"
        "models:\n"
        "  - name: mart_energy\n"
        "    description: Daily energy by building.\n"
        "    columns:\n"
        "      - {name: building_id, data_type: varchar, description: Building id, tests: [not_null, unique]}\n"
        "      - {name: kwh, data_type: double, description: Daily kWh}\n"
        "exposures:\n"
        "  - name: energy_dashboard\n"
        "    description: Carbon dashboard.\n"
        "    type: dashboard\n"
        "    owner: {name: estates-analytics}\n"
        "    depends_on: [ref('mart_energy')]\n",
        encoding="utf-8",
    )
    (models / "staging" / "stg_meter__hh.sql").write_text(
        "select meter_id, value_kwh as kwh from {{ source('meter', 'hh_a') }}\n", encoding="utf-8"
    )
    (models / "marts" / "mart_energy.sql").write_text(
        "{{ config(materialized='table') }}\n"
        "select b.building_id, sum(s.kwh) as kwh\n"
        "from {{ ref('stg_meter__hh') }} s\n"
        "join {{ ref('dim_building') }} b using (building_id)\n"
        "group by 1\n",
        encoding="utf-8",
    )
    return models
