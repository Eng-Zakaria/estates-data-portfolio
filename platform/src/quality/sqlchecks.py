"""P03 SQL check engine: evaluate ``sql_checked``/``sql_failed`` on DuckDB views.

Convention (documented per check in YAML):
- ``sql_checked``: scalar query returning rows_checked.
- ``sql_failed``: query returning violating rows; rows_failed = full count,
  with the first 100 kept as samples for ``dq.failed_rows``.
- ``failed_is_scalar: true``: ``sql_failed`` returns one number (count-based
  checks such as reconciliation); the single diagnostic row is stored as the
  sample when the count is non-zero.
- ``by_building`` (+ ``building_col`` in the failed rows +
  ``sql_checked_by_building`` returning (building_id, n) rows): per-building
  (checked, failed) pairs for building scores.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import duckdb

from .spec import CheckSpec

SAMPLE_LIMIT = 100


@dataclass
class SqlResult:
    check_id: str
    rows_checked: int
    rows_failed: int
    samples: list[dict] = field(default_factory=list)
    by_building: dict[str, dict[str, int]] | None = None

    @property
    def pass_rate(self) -> float:
        if self.rows_checked <= 0:
            return 1.0
        return max(0.0, 1.0 - self.rows_failed / self.rows_checked)


def _columns(con: duckdb.DuckDBPyConnection, sql: str) -> list[str]:
    return [d[0] for d in con.execute(f"SELECT * FROM ({sql}) LIMIT 0").description]


def evaluate(
    con: duckdb.DuckDBPyConnection,
    spec: CheckSpec,
    limit: int = SAMPLE_LIMIT,
) -> SqlResult:
    """Run one SQL check; raises on SQL errors (loud, never silent)."""
    assert spec.engine == "sql", spec.id
    checked_raw = con.execute(spec.sql_checked).fetchone()[0]
    rows_checked = int(checked_raw) if checked_raw is not None else 0
    if spec.failed_is_scalar:
        failed_raw = con.execute(spec.sql_failed).fetchone()[0]
        rows_failed = int(failed_raw) if failed_raw is not None else 0
        samples: list[dict] = []
        if rows_failed:
            cols = _columns(con, spec.sql_failed)
            row = con.execute(spec.sql_failed).fetchone()
            samples = [dict(zip(cols, [str(v) for v in row], strict=True))]
        return SqlResult(spec.id, rows_checked, rows_failed, samples)
    cols = _columns(con, spec.sql_failed)
    rows_failed = int(con.execute(f"SELECT COUNT(*) FROM ({spec.sql_failed})").fetchone()[0])
    raw = con.execute(f"SELECT * FROM ({spec.sql_failed}) LIMIT {limit}").fetchall()
    samples = [{c: (None if v is None else str(v)) for c, v in zip(cols, r, strict=True)} for r in raw]
    by_building = None
    if spec.by_building and spec.building_col and spec.building_col in cols:
        assert spec.sql_checked_by_building is not None, spec.id
        agg: dict[str, dict[str, int]] = {}
        counts = con.execute(f"SELECT {spec.building_col}, COUNT(*) FROM ({spec.sql_failed}) GROUP BY 1").fetchall()
        for building, n in counts:
            key = str(building) if building is not None else "__null__"
            agg[key] = {"checked": 0, "failed": int(n)}
        for building, n in con.execute(spec.sql_checked_by_building).fetchall():
            key = str(building) if building is not None else "__null__"
            agg.setdefault(key, {"checked": 0, "failed": 0})["checked"] = int(n)
        by_building = {k: v for k, v in agg.items() if v["checked"] > 0 or v["failed"] > 0}
    return SqlResult(spec.id, rows_checked, rows_failed, samples, by_building)


def status_of(pass_rate: float, threshold: float) -> str:
    return "pass" if pass_rate * 100.0 >= threshold else "fail"


def row_to_json(row: dict) -> str:
    return json.dumps(row, sort_keys=True)
