"""P02 ops export: ops.pipeline_runs -> CSV evidence.

Usage: python platform/orchestration/scripts/export_runs.py [--out PATH]
"""

from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="platform/orchestration/docs/pipeline_runs.csv")
    ap.add_argument("--db", default="data/pipeline_ops.duckdb")
    args = ap.parse_args()
    import duckdb

    db = REPO / args.db
    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db), read_only=True)
    try:
        con.execute(f"COPY (SELECT * FROM ops.pipeline_runs ORDER BY ts) TO '{out}' (HEADER, DELIMITER ',')")
        n = con.execute("SELECT COUNT(*) FROM ops.pipeline_runs").fetchone()[0]
    finally:
        con.close()
    print(f"exported {n} runs -> {out}")


if __name__ == "__main__":
    main()
