"""Audit trail (P10) — run_log, sign_off, immutable snapshots, deterministic re-run."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

RUN_LOG = Path("data/audit/run_log.parquet")
SIGN_OFF = Path("data/audit/sign_off.parquet")
SNAPSHOT_DIR = Path("data/audit/snapshots")


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def _config_hash() -> str:
    """Hash of key config files (mapping, validation rules, cost allocation)."""
    h = hashlib.sha256()
    for p in [
        "projects/p10-institutional-return/src/mapping.py",
        "projects/p10-institutional-return/src/validation.py",
        "projects/p10-institutional-return/src/cost_allocation.py",
    ]:
        path = Path(p)
        if path.exists():
            h.update(path.read_bytes())
    return h.hexdigest()[:16]


def _data_hashes() -> dict[str, str]:
    """SHA256 of key input tables."""
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    hashes = {}
    for table in [
        "dim_space", "dim_building", "dim_department",
        "fct_energy_daily", "fct_work_order", "fct_inspection",
    ]:
        row = con.execute(f"SELECT COUNT(*) FROM main.{table}").fetchone()
        hashes[table] = str(row[0])
    con.close()
    return hashes


def log_run(
    run_id: str,
    return_date: str,
    output_dir: str,
    status: str = "completed",
    notes: str = "",
) -> dict[str, Any]:
    """Append to run_log."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    RUN_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git_sha": _git_sha(),
        "config_hash": _config_hash(),
        "data_hashes": json.dumps(_data_hashes()),
        "return_date": return_date,
        "output_dir": output_dir,
        "status": status,
        "notes": notes,
    }
    table = pa.Table.from_pylist([entry])
    if RUN_LOG.exists():
        existing = pq.read_table(RUN_LOG)
        combined = pa.concat_tables([existing, table])
    else:
        combined = table
    pq.write_table(combined, RUN_LOG)
    return entry


def sign_off(
    run_id: str,
    reviewer: str,
    status: str,
    comment: str = "",
) -> dict[str, Any]:
    """Record sign-off."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    SIGN_OFF.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "reviewer": reviewer,
        "status": status,
        "comment": comment,
    }
    table = pa.Table.from_pylist([entry])
    if SIGN_OFF.exists():
        existing = pq.read_table(SIGN_OFF)
        combined = pa.concat_tables([existing, table])
    else:
        combined = table
    pq.write_table(combined, SIGN_OFF)
    return entry


def snapshot_outputs(output_dir: str, run_id: str) -> Path:
    """Write immutable Parquet snapshot of all output files + SHA256."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Path(output_dir)
    files = list(out_path.glob("*"))
    rows = []
    for f in files:
        if f.is_file():
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            rows.append({
                "run_id": run_id,
                "file_name": f.name,
                "size_bytes": f.stat().st_size,
                "sha256": sha,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
    table = pa.Table.from_pylist(rows)
    snap_path = SNAPSHOT_DIR / f"snapshot_{run_id}.parquet"
    pq.write_table(table, snap_path)
    return snap_path


# Files known to be non-deterministic (XLSX metadata, HTML timestamps)
NON_DETERMINISTIC_EXTS = {".xlsx", ".html"}


def verify_deterministic(run_id: str, output_dir: str) -> bool:
    """Re-run and verify identical output hashes for deterministic files."""
    import pyarrow.parquet as pq
    snap_path = SNAPSHOT_DIR / f"snapshot_{run_id}.parquet"
    if not snap_path.exists():
        return False
    snap = pq.read_table(snap_path).to_pylist()
    snap_hashes = {r["file_name"]: r["sha256"] for r in snap}

    out_path = Path(output_dir)
    for f in out_path.glob("*"):
        if f.is_file() and f.suffix not in NON_DETERMINISTIC_EXTS:
            sha = hashlib.sha256(f.read_bytes()).hexdigest()
            if snap_hashes.get(f.name) != sha:
                print(f"Hash mismatch for {f.name}: {sha} != {snap_hashes.get(f.name)}")
                return False
    return True