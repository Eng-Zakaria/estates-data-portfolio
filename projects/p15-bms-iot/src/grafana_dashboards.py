"""Generate the Grafana dashboards for the P15 stack.

The dashboards are dashboards-as-code: `grafana/provisioning/dashboards/*.json`
is generated from the point registry so a panel never queries a point that no
longer exists, and `tests/test_grafana.py` asserts the committed files match.
Editing a JSON file by hand works until someone adds a plant item, at which
point the dashboard silently shows nothing for it.

Four dashboards, matching what an engineer on shift actually asks for:

* **Plant overview** - what is the plant doing right now, per building
* **Point health** - which points are stale, flat or reporting suspect values
* **Active faults** - open alerts plus the findings from the offline detector
* **Completeness** - data coverage as building x point_class, which is how a
  silent gap across a whole system becomes visible

    python src/grafana_dashboards.py
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from make_registry import BUILDINGS

REPO = Path(__file__).resolve().parent.parent
REGISTRY_CSV = Path(__file__).resolve().parent / "point_registry.csv"
OUT_DIR = REPO / "grafana" / "provisioning" / "dashboards"

DATASOURCE = {"type": "postgres", "uid": "p15-timescaledb"}
POINT_ID = "B001.ahu_01.supply_temp"

SCHEMA_VERSION = 39


def _panel(
    panel_id: int,
    title: str,
    kind: str,
    sql: str,
    x: int,
    y: int,
    w: int,
    h: int,
    unit: str = "short",
    legend: str | None = None,
    description: str = "",
) -> dict[str, object]:
    panel: dict[str, object] = {
        "id": panel_id,
        "type": kind,
        "title": title,
        "description": description,
        "datasource": DATASOURCE,
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "fieldConfig": {
            "defaults": {"unit": unit, "color": {"mode": "palette-classic"}, "custom": {}},
            "overrides": [],
        },
        "options": {},
    }
    if kind == "timeseries":
        panel["targets"] = [{"refId": "A", "format": "time_series", "rawSql": sql}]
        panel["fieldConfig"] = {
            "defaults": {
                "unit": unit,
                "color": {"mode": "palette-classic"},
                "custom": {
                    "drawStyle": "line",
                    "lineWidth": 1,
                    "fillOpacity": 5,
                    "showPoints": "never",
                    "spanNulls": False,
                },
            },
            "overrides": [],
        }
        panel["options"] = {"legend": {"displayMode": "list", "placement": "bottom", "calcs": ["mean", "max"]}}
        if legend:
            panel["legendFormat"] = legend
    elif kind == "stat":
        panel["targets"] = [{"refId": "A", "format": "table", "rawSql": sql}]
        panel["options"] = {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "colorMode": "value",
            "graphMode": "none",
        }
    elif kind == "table":
        panel["targets"] = [{"refId": "A", "format": "table", "rawSql": sql}]
        panel["options"] = {"showHeader": True, "cellHeight": "sm"}
    elif kind == "heatmap":
        panel["targets"] = [{"refId": "A", "format": "time_series", "rawSql": sql}]
        panel["options"] = {"calculate": False, "color": {"mode": "scheme", "scheme": "Spectral"}}
    return panel


def _dashboard(
    uid: str, title: str, description: str, panels: list[dict[str, object]], tags: list[str], time_from: str = "now-24h"
) -> dict[str, object]:
    return {
        "uid": uid,
        "title": title,
        "description": description,
        "tags": tags,
        "timezone": "Europe/London",
        "schemaVersion": SCHEMA_VERSION,
        "version": 1,
        "editable": True,
        "time": {"from": time_from, "to": "now"},
        "refresh": "1m",
        "templating": {"list": []},
        "panels": panels,
    }


def plant_overview() -> dict[str, object]:
    buildings = ", ".join(f"'{b}'" for b in BUILDINGS)
    panels = [
        _panel(
            1,
            "Supply air temperature by building",
            "timeseries",
            "SELECT bucket AS time, point_id AS metric, avg_value AS value\n"
            "  FROM bms.readings_15min\n"
            f" WHERE point_class = 'supply_temp' AND point_id LIKE ANY (ARRAY[{buildings} || '.%'])\n"
            " ORDER BY bucket",
            0,
            0,
            12,
            8,
            unit="celsius",
            legend="{{point_id}}",
            description="15-minute mean supply air temperature. A flat line while the plant is occupied is a stuck sensor or a stopped AHU.",
        ),
        _panel(
            2,
            "Fan speed and damper position",
            "timeseries",
            "SELECT bucket AS time, point_id AS metric, avg_value AS value\n"
            "  FROM bms.readings_15min\n"
            " WHERE point_class IN ('fan_speed', 'damper_pos')\n"
            " ORDER BY bucket",
            12,
            0,
            12,
            8,
            unit="percent",
            legend="{{point_id}}",
            description="Plant running state. Fan above 20% overnight on a weekday is the SEM-03 signature.",
        ),
        _panel(
            3,
            "Heating and cooling valve positions",
            "timeseries",
            "SELECT bucket AS time, point_id AS metric, avg_value AS value\n"
            "  FROM bms.readings_15min\n"
            " WHERE point_class IN ('heating_valve', 'cooling_valve')\n"
            " ORDER BY bucket",
            0,
            8,
            12,
            8,
            unit="percent",
            legend="{{point_id}}",
            description="Both valves above 20% on the same AHU at the same time is SEM-01 (simultaneous heating and cooling).",
        ),
        _panel(
            4,
            "Room conditions",
            "timeseries",
            "SELECT bucket AS time, point_id AS metric, avg_value AS value\n"
            "  FROM bms.readings_15min\n"
            " WHERE point_class IN ('room_temp', 'co2')\n"
            " ORDER BY bucket",
            12,
            8,
            12,
            8,
            unit="short",
            legend="{{point_id}}",
            description="Note the unit mismatch on purpose: Grafana applies one unit per panel, so this view is for shape, not absolute values. P17 is the CO2 analysis.",
        ),
        _panel(
            5,
            "Points reporting",
            "stat",
            "SELECT count(DISTINCT point_id) AS reporting FROM bms.readings\n WHERE ts > now() - INTERVAL '15 minutes'",
            0,
            16,
            4,
            4,
            description="Distinct points seen in the last 15 minutes. Below the registry count means something has gone quiet.",
        ),
        _panel(
            6,
            "Dead-lettered messages",
            "stat",
            "SELECT count(*) AS dead FROM bms.dead_letter WHERE ts > now() - INTERVAL '24 hours'",
            4,
            16,
            4,
            4,
            description="Messages rejected by the ingestion contract in the last 24 hours. Non-zero is expected (the simulator injects them); a sudden rise is not.",
        ),
        _panel(
            7,
            "Sub-metered energy",
            "timeseries",
            "SELECT bucket AS time, sum(sum_value) AS value\n"
            "  FROM bms.readings_daily\n"
            " WHERE point_class = 'sub_meter_kwh'\n"
            " GROUP BY bucket\n"
            " ORDER BY bucket",
            8,
            16,
            16,
            8,
            unit="kWh",
            legend="total",
            description="Summed across plant. The daily aggregate keeps the sum, which is meaningless for temperatures.",
        ),
    ]
    return _dashboard(
        "p15-plant-overview",
        "BMS Plant Overview (synthetic)",
        "Synthetic BMS telemetry. Every value on this dashboard comes from the simulator; nothing here describes a real building.",
        panels,
        ["p15", "bms", "synthetic"],
    )


def point_health() -> dict[str, object]:
    panels = [
        _panel(
            1,
            "Points not healthy",
            "table",
            "SELECT point_id, building, point_class, samples_24h, completeness_pct, last_seen, good_pct\n"
            "  FROM bms.v_point_health\n"
            " WHERE completeness_pct < 100 OR good_pct < 100\n"
            " ORDER BY completeness_pct ASC\n"
            " LIMIT 100",
            0,
            0,
            24,
            9,
            description="The triage list: any point below full coverage, or carrying suspect-quality values. Sorted worst first.",
        ),
        _panel(
            2,
            "Completeness by building and point class",
            "heatmap",
            "SELECT bucket AS time, building || ' / ' || point_class AS metric, completeness_pct AS value\n"
            "  FROM bms.v_completeness\n"
            " ORDER BY building, point_class",
            0,
            9,
            12,
            8,
            unit="percent",
            description="A whole point class flat at zero for one building is a controller or network segment that has stopped reporting, not a data quality blip.",
        ),
        _panel(
            3,
            "Longest gaps in the last day",
            "table",
            "SELECT point_id, max_gap_minutes\n"
            "  FROM bms.v_point_health\n"
            " WHERE max_gap_minutes IS NOT NULL\n"
            " ORDER BY max_gap_minutes DESC\n"
            " LIMIT 20",
            12,
            9,
            12,
            8,
            unit="m",
            description="Staleness is the first thing to check when a dashboard looks suspiciously flat.",
        ),
        _panel(
            4,
            "Suspect quality share",
            "timeseries",
            "SELECT bucket AS time, point_id AS metric,\n"
            "       100.0 * count(*) FILTER (WHERE quality = 'suspect') / NULLIF(count(*), 0) AS value\n"
            "  FROM bms.readings\n"
            " WHERE ts > now() - INTERVAL '24 hours'\n"
            " GROUP BY bucket, point_id\n"
            " ORDER BY bucket",
            0,
            17,
            24,
            8,
            unit="percent",
            legend="{{point_id}}",
            description="Suspect values are accepted, not dropped: the pipeline records them so an operator can decide. A rising share means the plant is reporting trouble, not that the pipeline is broken.",
        ),
    ]
    return _dashboard(
        "p15-point-health",
        "BMS Point Health (synthetic)",
        "Staleness, completeness and comms quality per point. Synthetic data.",
        panels,
        ["p15", "bms", "synthetic", "monitoring"],
    )


def active_faults() -> dict[str, object]:
    panels = [
        _panel(
            1,
            "Open alerts",
            "table",
            "SELECT point_id, alert_type, severity, ts, detail\n"
            "  FROM bms.alerts\n"
            " WHERE resolved_at IS NULL\n"
            " ORDER BY ts DESC",
            0,
            0,
            12,
            8,
            description="Raised by the Node-RED staleness check every 5 minutes. One open row per point and alert type.",
        ),
        _panel(
            2,
            "Alert volume by type",
            "timeseries",
            "SELECT ts AS time, alert_type AS metric, count(*) AS value\n"
            "  FROM bms.alerts\n"
            " WHERE ts > now() - INTERVAL '24 hours'\n"
            " GROUP BY ts, alert_type\n"
            " ORDER BY ts",
            12,
            0,
            12,
            8,
            unit="short",
            legend="{{alert_type}}",
        ),
        _panel(
            3,
            "Dead letter by reason",
            "table",
            "SELECT reason, count(*) AS n, max(ts) AS latest\n"
            "  FROM bms.dead_letter\n"
            " WHERE ts > now() - INTERVAL '24 hours'\n"
            " GROUP BY reason\n"
            " ORDER BY n DESC",
            0,
            8,
            12,
            8,
            description="Why messages were rejected. A new reason code appearing is the signal to look at a controller's configuration.",
        ),
        _panel(
            4,
            "Dead letter sample payloads",
            "table",
            "SELECT ts, topic, reason, left(payload, 120) AS payload\n"
            "  FROM bms.dead_letter\n"
            " ORDER BY ts DESC\n"
            " LIMIT 25",
            12,
            8,
            12,
            8,
            description="Enough of the payload to identify the device without dumping a whole history into the dashboard.",
        ),
        _panel(
            5,
            "Findings by rule (offline detector)",
            "table",
            "SELECT rule_id, count(*) AS findings, count(DISTINCT point_id) AS points\n"
            "  FROM bms.findings\n"
            " WHERE start_ts > now() - INTERVAL '24 hours'\n"
            " GROUP BY rule_id\n"
            " ORDER BY findings DESC",
            0,
            16,
            12,
            8,
            description="SEM-01..05 from the batch detector in src/health.py, loaded by `make iot-load-findings`.",
        ),
        _panel(
            6,
            "Findings detail",
            "table",
            "SELECT start_ts, end_ts, rule_id, point_id, samples, detail\n"
            "  FROM bms.findings\n"
            " WHERE start_ts > now() - INTERVAL '24 hours'\n"
            " ORDER BY start_ts DESC\n"
            " LIMIT 50",
            12,
            16,
            12,
            8,
            description="One row per detected window, with the evidence in plain words.",
        ),
    ]
    return _dashboard(
        "p15-active-faults",
        "BMS Active Faults (synthetic)",
        "Open alerts, dead-letter reasons and detected fault windows. Synthetic data.",
        panels,
        ["p15", "bms", "synthetic", "monitoring"],
    )


def completeness() -> dict[str, object]:
    panels = [
        _panel(
            1,
            "Coverage heatmap",
            "heatmap",
            "SELECT bucket AS time, building || ' / ' || point_class AS metric, completeness_pct AS value\n"
            "  FROM bms.v_completeness\n"
            " ORDER BY building, point_class",
            0,
            0,
            24,
            10,
            unit="percent",
            description="Expected samples vs actual, per building and point class. This is the panel that catches a gateway that stopped talking to one controller.",
        ),
        _panel(
            2,
            "Messages ingested per hour",
            "timeseries",
            "SELECT time_bucket(INTERVAL '1 hour', ts) AS time, count(*) AS value\n"
            "  FROM bms.readings\n"
            " WHERE ts > now() - INTERVAL '24 hours'\n"
            " GROUP BY 1\n"
            " ORDER BY 1",
            0,
            10,
            12,
            8,
            unit="short",
            description="Throughput. A step change here means points stopped arriving, not that the plant stopped.",
        ),
        _panel(
            3,
            "Dead letter per hour",
            "timeseries",
            "SELECT time_bucket(INTERVAL '1 hour', ts) AS time, count(*) AS value\n"
            "  FROM bms.dead_letter\n"
            " WHERE ts > now() - INTERVAL '24 hours'\n"
            " GROUP BY 1\n"
            " ORDER BY 1",
            12,
            10,
            12,
            8,
            unit="short",
            description="Rejections over the same window, so the two charts can be read together.",
        ),
    ]
    return _dashboard(
        "p15-completeness",
        "BMS Data Completeness (synthetic)",
        "Is the data complete enough to trust the dashboards built on it? Synthetic data.",
        panels,
        ["p15", "bms", "synthetic", "monitoring"],
    )


DASHBOARDS: dict[str, Callable[[], dict[str, object]]] = {
    "plant_overview.json": plant_overview,
    "point_health.json": point_health,
    "active_faults.json": active_faults,
    "completeness.json": completeness,
}


def write_all(out_dir: Path = OUT_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, builder in DASHBOARDS.items():
        path = out_dir / name
        dashboard = builder()
        path.write_text(json.dumps(dashboard, indent=2) + "\n", encoding="utf-8", newline="\n")
        written.append(path)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    # touching the registry here fails fast if it is missing, rather than
    # leaving a half-written dashboard set
    if not REGISTRY_CSV.exists():
        parser.error(f"point registry not found: {REGISTRY_CSV} (run `python src/make_registry.py`)")
    for path in write_all(args.out):
        dashboard = json.loads(path.read_text(encoding="utf-8"))
        print(f"{path.name}: {len(dashboard['panels'])} panels -> {path}")


if __name__ == "__main__":
    main()
