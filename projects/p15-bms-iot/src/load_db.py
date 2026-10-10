"""Load the offline pipeline's Parquet outputs into TimescaleDB.

The simulator publishes over MQTT and Node-RED writes `bms.readings`, but the
fault detector in `src/health.py` is a batch job. This loader is the bridge: it
takes the accepted readings, the dead-letter rows, the registry and the findings
and upserts them, so `make iot-demo` gives the Grafana dashboards something to
show without waiting for a full simulated day at speed.

Connects with psycopg (P15's only non-stdlib runtime dependency beyond pandas),
and is a no-op-friendly upsert so re-running it does not duplicate rows.

    python src/load_db.py --data data/p15
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from validate import load_registry

READINGS = "bms.readings"
POINTS = "bms.points"
DEAD = "bms.dead_letter"
FINDINGS = "bms.findings"


def dsn_from_env() -> str:
    """libpq connection string from the environment.

    The host defaults to localhost and the port to 5433, matching the port the
    demo stack publishes (5432 belongs to the Airflow stack in this repo).
    """
    return (
        f"host={os.environ.get('PGHOST', 'localhost')} "
        f"port={os.environ.get('PGPORT', '5433')} "
        f"dbname={os.environ.get('PGDATABASE', 'bms_db')} "
        f"user={os.environ.get('PGUSER', 'bms_user')} "
        f"password={os.environ.get('PGPASSWORD', 'bms_pass')}"
    )


if TYPE_CHECKING:  # pragma: no cover - import cycle avoidance for the type only
    from psycopg import Connection


def _connect(dsn: str) -> Connection:
    import psycopg

    return psycopg.connect(dsn)


def load_points(conn: Connection, registry_csv: Path) -> int:
    rows = list(load_registry(str(registry_csv)).values())
    sql = """
        INSERT INTO bms.points
            (point_id, building, system, equipment, equipment_kind, point_class, unit, source_address)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (point_id) DO UPDATE SET
            building = EXCLUDED.building,
            system = EXCLUDED.system,
            equipment = EXCLUDED.equipment,
            equipment_kind = EXCLUDED.equipment_kind,
            point_class = EXCLUDED.point_class,
            unit = EXCLUDED.unit,
            source_address = EXCLUDED.source_address
    """
    with conn.cursor() as cur:
        cur.executemany(
            sql,
            [
                (
                    r["point_id"],
                    r["building"],
                    r["system"],
                    r["equipment"],
                    r["equipment_kind"],
                    r["point_class"],
                    r["unit"],
                    r["source_address"],
                )
                for r in rows
            ],
        )
    return len(rows)


def load_readings(conn: Connection, accepted: pd.DataFrame) -> int:
    """Upsert accepted readings. Redelivery is normal (at-least-once MQTT), so
    the same (ts, point_id) is an update rather than a duplicate."""
    sql = """
        INSERT INTO bms.readings (ts, point_id, value, unit, quality)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (ts, point_id) DO UPDATE SET
            value = EXCLUDED.value,
            unit = EXCLUDED.unit,
            quality = EXCLUDED.quality
    """
    rows = [
        (
            pd.Timestamp(str(r.ts)),
            str(r.point_id),
            float(str(r.value)),
            str(r.unit),
            str(r.quality),
        )
        for r in accepted.itertuples()
    ]
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)


def load_dead_letter(conn: Connection, dead: pd.DataFrame) -> int:
    sql = """
        INSERT INTO bms.dead_letter (ts, topic, payload, reason, point_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    rows = [
        (
            pd.Timestamp(str(r.ts)).isoformat() if not pd.isna(r.ts) else None,
            str(r.topic),
            str(r.payload),
            str(r.reason),
            None,
        )
        for r in dead.itertuples()
    ]
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)


def load_findings(conn: Connection, findings: pd.DataFrame) -> int:
    sql = """
        INSERT INTO bms.findings (start_ts, end_ts, rule_id, point_id, samples, detail)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (start_ts, rule_id, point_id) DO UPDATE SET
            end_ts = EXCLUDED.end_ts,
            samples = EXCLUDED.samples,
            detail = EXCLUDED.detail
    """
    rows = [
        (
            str(r.start_ts),
            str(r.end_ts),
            str(r.rule_id),
            str(r.point_id),
            int(float(str(r.samples))),
            str(r.detail),
        )
        for r in findings.itertuples()
    ]
    if not rows:
        return 0
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    return len(rows)


def load_all(data_dir: Path, registry_csv: Path, dsn: str) -> dict[str, int]:
    accepted = pd.read_parquet(data_dir / "bms_readings_accepted.parquet")
    dead = pd.read_parquet(data_dir / "bms_dead_letter.parquet")
    findings = pd.read_parquet(data_dir / "bms_findings.parquet")
    with _connect(dsn) as conn:
        counts = {
            "points": load_points(conn, registry_csv),
            "readings": load_readings(conn, accepted),
            "dead_letter": load_dead_letter(conn, dead),
            "findings": load_findings(conn, findings),
        }
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/p15"))
    parser.add_argument("--registry", type=Path, default=Path("src/point_registry.csv"))
    parser.add_argument("--dsn", default=None, help="defaults to the .env.example host/port values")
    args = parser.parse_args()
    counts = load_all(args.data, args.registry, args.dsn or dsn_from_env())
    for table, n in counts.items():
        print(f"{table}: {n}")


if __name__ == "__main__":
    main()
