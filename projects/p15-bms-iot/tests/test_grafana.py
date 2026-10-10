"""Grafana dashboards-as-code: the committed JSON must match the generator and
the queries must match the schema."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from grafana_dashboards import DASHBOARDS, OUT_DIR, write_all


@pytest.fixture(scope="module")
def committed() -> dict[str, dict]:
    return {name: json.loads((OUT_DIR / name).read_text(encoding="utf-8")) for name in DASHBOARDS}


def test_all_four_dashboards_are_committed():
    for name in DASHBOARDS:
        assert (OUT_DIR / name).exists(), name


def test_committed_dashboards_match_the_generator(tmp_path, committed):
    """The dashboards are generated from the registry; a hand-edit or a stale
    copy would show a panel for a point that no longer exists."""
    written = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in write_all(tmp_path)}
    assert written == committed


def test_dashboards_are_labelled_synthetic(committed):
    """Rule 2 of AGENTS.md: synthetic data must be labelled as such on the
    dashboard, not only in the README."""
    for name, dashboard in committed.items():
        assert "synthetic" in dashboard["title"].lower(), name
        assert "synthetic" in dashboard["description"].lower(), name
        assert "synthetic" in dashboard["tags"], name


def test_every_panel_has_a_unique_id_within_its_dashboard(committed):
    for name, dashboard in committed.items():
        ids = [p["id"] for p in dashboard["panels"]]
        assert len(ids) == len(set(ids)), name


def test_every_panel_targets_the_provisioned_datasource(committed):
    for name, dashboard in committed.items():
        for panel in dashboard["panels"]:
            assert panel["datasource"]["uid"] == "p15-timescaledb", (name, panel["title"])


def test_every_query_selects_from_the_bms_schema(committed):
    for name, dashboard in committed.items():
        for panel in dashboard["panels"]:
            sql = panel["targets"][0]["rawSql"]
            assert re.search(r"FROM bms\.", sql), (name, panel["title"])


def test_queries_reference_objects_that_exist_in_the_schema(project, committed):
    """A dashboard querying a table the migration never creates renders an empty
    panel with no error, which is worse than a failure."""
    schema = (project / "src" / "schema.sql").read_text(encoding="utf-8")
    defined = set(re.findall(r"CREATE (?:MATERIALIZED VIEW|TABLE|OR REPLACE VIEW)[^\n]*?bms\.(\w+)", schema))
    defined |= set(re.findall(r"CREATE OR REPLACE VIEW bms\.(\w+)", schema))
    for name, dashboard in committed.items():
        for panel in dashboard["panels"]:
            for table in set(re.findall(r"FROM bms\.(\w+)", panel["targets"][0]["rawSql"])):
                assert table in defined, (
                    f"{name}/{panel['title']} queries bms.{table}, which schema.sql does not create"
                )


def test_dashboards_use_site_local_timezone(committed):
    for dashboard in committed.values():
        assert dashboard["timezone"] == "Europe/London"


def test_dashboards_default_to_the_last_24_hours(committed):
    for dashboard in committed.values():
        assert dashboard["time"]["from"] == "now-24h"


def test_the_four_documented_questions_each_have_a_dashboard(committed):
    titles = " ".join(d["title"].lower() for d in committed.values())
    for topic in ("plant", "health", "fault", "completeness"):
        assert topic in titles, topic


def test_point_health_dashboard_surfaces_staleness_and_completeness(committed):
    panels = " ".join(p["title"].lower() for p in committed["point_health.json"]["panels"])
    assert "completeness" in panels
    assert "gap" in panels or "stale" in panels


def test_active_faults_dashboard_covers_alerts_and_dead_letter(committed):
    panels = " ".join(p["title"].lower() for p in committed["active_faults.json"]["panels"])
    assert "alert" in panels
    assert "dead letter" in panels


def test_energy_panel_sums_kwh_not_temperatures(committed):
    """The daily aggregate keeps sum_value; using it on a temperature point
    would produce a meaningless number."""
    panel = next(p for p in committed["plant_overview.json"]["panels"] if p["title"] == "Sub-metered energy")
    assert "sum(sum_value)" in panel["targets"][0]["rawSql"]
    assert "sub_meter_kwh" in panel["targets"][0]["rawSql"]


def test_only_the_energy_panel_uses_a_sum_aggregate(committed):
    """Summing temperatures is meaningless; summing kWh is the whole point of
    the daily rollup, so exactly one panel may use SUM."""
    summed = [
        p["title"] for p in committed["plant_overview.json"]["panels"] if "sum(" in p["targets"][0]["rawSql"].lower()
    ]
    assert summed == ["Sub-metered energy"]


def test_dashboards_have_no_hardcoded_credentials(committed):
    for name, dashboard in committed.items():
        raw = json.dumps(dashboard)
        for banned in ("password", "bms_pass", "admin"):
            assert banned not in raw.lower(), (name, banned)


def test_regenerating_is_idempotent(tmp_path):
    first = {p.name: p.read_bytes() for p in write_all(tmp_path)}
    second = {p.name: p.read_bytes() for p in write_all(tmp_path)}
    assert first == second


def test_out_dir_defaults_into_the_provisioning_folder():
    assert OUT_DIR.name == "dashboards"
    assert OUT_DIR.parent.name == "provisioning"
    assert OUT_DIR == Path(OUT_DIR)
