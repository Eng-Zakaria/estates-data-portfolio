"""P02 Airflow task logic (pure Python, NO airflow imports).

Kept airflow-free so unit tests run on any host (the local Windows env cannot
import airflow). DAG files in ../dags/ only wire these functions into operators.
All paths resolve from env with repo-root defaults so the same code runs on the
host, in CI and inside the compose containers (repo mounted at /opt/repo).
"""

from __future__ import annotations

import json
import os
import shutil
import smtplib
import subprocess
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

REPO = Path(os.environ.get("ESTATES_REPO", ".")).resolve()
LANDING = Path(os.environ.get("ESTATES_LANDING", str(REPO / "data" / "landing")))
LAKE = Path(os.environ.get("ESTATES_LAKE", str(REPO / "data" / "lakehouse")))
TRUTH = Path(os.environ.get("ESTATES_TRUTH", str(REPO / "data" / "truth")))
OPS_DB = Path(os.environ.get("ESTATES_OPS_DB", str(REPO / "data" / "pipeline_ops.duckdb")))
GOLD_DIR = Path(os.environ.get("ESTATES_GOLD", str(REPO / "data" / "gold")))
WAREHOUSE_DB = Path(os.environ.get("ESTATES_WAREHOUSE", str(REPO / "data" / "warehouse.duckdb")))
CONTRACTS_DIR = REPO / "platform" / "contracts"
MAIL_HOST = os.environ.get("ESTATES_MAIL_HOST", "mailpit")
MAIL_PORT = int(os.environ.get("ESTATES_MAIL_PORT", "1025"))
MAIL_TO = os.environ.get("ESTATES_MAIL_TO", "estates-ops@example.org")

SOURCE_FILE_PATTERNS = {
    "space_register": "space_register_*.xlsx",
    "cafm_workorders": "cafm_workorders_*.csv",
    "meter_hh_supplierA": "meter_hh_supplierA_*.csv",
    "meter_hh_supplierB": "meter_hh_supplierB_*.csv",
    "bms_trends": "bms_trends_*.csv",
    "statutory_inspections": "statutory_inspections_*.xlsx",
    "timetable": "timetable_*.csv",
    "sensors": "sensors_*.parquet",
}


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def list_landing_files(source: str, landing: Path = LANDING) -> list[str]:
    pattern = SOURCE_FILE_PATTERNS[source]
    return sorted(str(p) for p in landing.glob(pattern))


def read_header_columns(path: str) -> list[str]:
    """Best-effort header read for drift detection (csv/xlsx/parquet)."""
    import pandas as pd

    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return list(pd.read_csv(path, nrows=0).columns)
    if suffix in (".xlsx", ".xls"):
        # Space register has two merged title rows; headers live on row 3.
        try:
            return list(pd.read_excel(path, nrows=0, header=2).columns)
        except Exception:
            return list(pd.read_excel(path, nrows=0).columns)
    if suffix == ".parquet":
        return list(pd.read_parquet(path).columns[:0])
    raise ValueError(f"unsupported landing file type: {path}")


def contract_columns(source: str) -> list[str]:
    import yaml

    doc = yaml.safe_load((CONTRACTS_DIR / f"{source}.yml").read_text(encoding="utf-8"))
    return [str(c["name"]) for c in doc.get("columns", [])]


def check_schema_drift(source: str, path: str) -> dict:
    """Compare landing-file columns to the contract. Never raises on drift."""
    expected = contract_columns(source)
    try:
        actual = [str(c) for c in read_header_columns(path)]
    except Exception as exc:
        return {"source": source, "file": path, "drift": True, "error": str(exc),
                "added": [], "missing": expected}
    added = [c for c in actual if c not in expected]
    missing = [c for c in expected if c not in actual]
    return {"source": source, "file": path, "drift": bool(added or missing),
            "added": added, "missing": missing}


def quarantine_landing_file(source: str, path: str, reason: str) -> str:
    dest_dir = LAKE / "quarantine_files" / source
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{Path(path).stem}__quarantined{Path(path).suffix}"
    shutil.move(path, dest)
    (dest_dir / f"{dest.stem}.reason.txt").write_text(
        f"{utcnow_iso()} {reason}\n", encoding="utf-8"
    )
    return str(dest)


def ingest_file(source: str, path: str, lake: Path = LAKE, truth: Path = TRUTH) -> dict:
    """Bronze one landing file, then re-silver the source. Idempotent via checksum."""
    from ingest.bronze import load_bronze
    from ingest.cli import _run_silver_one

    t0 = time.monotonic()
    root = lake
    dest, entry = load_bronze(source, Path(path), root / "bronze")
    silver_n, quar_n = (0, 0)
    if entry.get("status") != "skipped":
        silver_n, quar_n = _run_silver_one(source, root, truth / "buildings.parquet")
    return {"source": source, "file": path, "bronze_dest": str(dest),
            "bronze_status": entry.get("status"), "bronze_rows": entry.get("rows"),
            "silver_rows": silver_n, "quarantine_rows": quar_n,
            "duration_s": round(time.monotonic() - t0, 2)}


def load_watermark(source: str) -> dict:
    state_file = LAKE / "watermarks" / f"{source}.json"
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return {"source": source, "last_processed": None, "files": []}


def save_watermark(source: str, state: dict) -> None:
    state_file = LAKE / "watermarks" / f"{source}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")


def new_files_since(source: str, watermark: dict, landing: Path = LANDING) -> list[str]:
    seen = set(watermark.get("files", []))
    return [f for f in list_landing_files(source, landing) if f not in seen]


def ops_connect(db_path: Path = OPS_DB):
    import duckdb

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute(
        "CREATE SCHEMA IF NOT EXISTS ops; "
        "CREATE TABLE IF NOT EXISTS ops.pipeline_runs ("
        "dag_id VARCHAR, task_id VARCHAR, run_id VARCHAR, "
        "data_interval_start VARCHAR, status VARCHAR, duration_s DOUBLE, "
        "rows_in BIGINT, rows_out BIGINT, error VARCHAR, ts VARCHAR)"
    )
    return con


def record_run(row: dict, db_path: Path = OPS_DB) -> None:
    con = ops_connect(db_path)
    try:
        con.execute(
            "INSERT INTO ops.pipeline_runs VALUES (?,?,?,?,?,?,?,?,?,?)",
            [row.get("dag_id"), row.get("task_id"), row.get("run_id"),
             row.get("data_interval_start"), row.get("status"),
             row.get("duration_s"), row.get("rows_in"), row.get("rows_out"),
             row.get("error"), utcnow_iso()],
        )
    finally:
        con.close()


def send_alert(subject: str, body: str) -> bool:
    """Mail via Mailpit sink. Never raises (a dead alerter must not fail the callback)."""
    try:
        msg = EmailMessage()
        msg["From"] = "airflow@estates.local"
        msg["To"] = MAIL_TO
        msg["Subject"] = f"[estates-airflow] {subject}"
        msg.set_content(body)
        with smtplib.SMTP(MAIL_HOST, MAIL_PORT, timeout=10) as smtp:
            smtp.send_message(msg)
        return True
    except Exception:
        return False


def run_dbt_build(repo: Path = REPO) -> dict:
    t0 = time.monotonic()
    proc = subprocess.run(
        ["dbt", "build", "--profiles-dir", "platform/dbt",
         "--project-dir", "platform/dbt", "--target", "dev"],
        cwd=str(repo), capture_output=True, text=True,
    )
    return {"returncode": proc.returncode, "duration_s": round(time.monotonic() - t0, 1),
            "tail": (proc.stdout + proc.stderr)[-2000:]}


def dq_checkpoint(repo: Path = REPO) -> dict:
    """P03 hook: run the quality gate when platform/quality lands, else skip loudly."""
    runner = repo / "platform" / "quality" / "run.py"
    if not runner.exists():
        return {"status": "skipped",
                "notice": "platform/quality not built yet (P03); gate enforced by P05 dq_gate."}
    proc = subprocess.run(["python", str(runner), "--fail-on", "error"],
                          cwd=str(repo), capture_output=True, text=True)
    return {"status": "pass" if proc.returncode == 0 else "fail",
            "returncode": proc.returncode, "tail": (proc.stdout + proc.stderr)[-2000:]}


def publish_gold(
    warehouse: Path = WAREHOUSE_DB, gold_dir: Path = GOLD_DIR,
) -> dict:
    """Export contracted mart tables to data/gold for the P06-P10 handoffs."""
    import duckdb

    tables = ["dim_building", "dim_space", "dim_asset", "dim_meter", "dim_date",
              "fct_meter_hh", "fct_energy_daily", "fct_work_order", "fct_inspection",
              "fct_timetable_event", "fct_sensor_15min", "mart_space_utilisation",
              "mart_asset_health", "mart_carbon_monthly", "mart_compliance_status",
              "mart_dq_scorecard"]
    gold_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(warehouse), read_only=True)
    exported = {}
    try:
        existing = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        for table in tables:
            if table not in existing:
                continue
            out = gold_dir / f"{table}.parquet"
            con.execute(f"COPY (SELECT * FROM {table}) TO '{out}' (FORMAT PARQUET)")
            exported[table] = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        con.close()
    return {"gold_dir": str(gold_dir), "tables": exported}


def housekeeping(
    landing: Path = LANDING, lake: Path = LAKE,
    landing_retention_days: int = 30, ops_retention_days: int = 90,
    db_path: Path = OPS_DB,
) -> dict:
    """Archive old landing files; prune ops history. Returns counts."""
    import datetime as dt

    now = time.time()
    archived = 0
    archive_root = lake / "archive"
    for path in landing.rglob("*"):
        if path.is_file() and now - path.stat().st_mtime > landing_retention_days * 86400:
            dest = archive_root / path.relative_to(landing)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest))
            archived += 1
    cutoff = (dt.datetime.now(timezone.utc) - dt.timedelta(days=ops_retention_days)).isoformat()
    con = ops_connect(db_path)
    try:
        con.execute("DELETE FROM ops.pipeline_runs WHERE ts < ?", [cutoff])
        pruned = con.execute("SELECT COUNT(*) FROM ops.pipeline_runs").fetchone()[0]
    finally:
        con.close()
    return {"archived_landing_files": archived, "ops_rows_kept": pruned}
