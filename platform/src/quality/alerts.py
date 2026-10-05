"""P03 alerts: score drops and error failures recorded to dq.alerts.

- Any ``error``-severity check with status fail raises an ``error_fail`` alert.
- A dataset score dropping more than 5 points vs its trailing-7-run mean
  raises a ``score_drop`` alert (first runs seed the baseline silently).
The runner prints a digest; P02/P05 consume the exit code and dq.alerts.
"""

from __future__ import annotations

import duckdb

DROP_POINTS = 5.0
HISTORY_RUNS = 7


def trailing_mean(con: duckdb.DuckDBPyConnection, grain: str, dataset: str, key: str = "") -> float | None:
    rows = con.execute(
        "SELECT score FROM dq.scores WHERE grain = ? AND dataset = ? AND key = ? ORDER BY run_id DESC LIMIT ?",
        [grain, dataset, key, HISTORY_RUNS],
    ).fetchall()
    if not rows:
        return None
    return sum(r[0] for r in rows) / len(rows)


def evaluate_alerts(
    con: duckdb.DuckDBPyConnection,
    run_id: str,
    dataset_scores: dict[str, float],
    error_fails: list[tuple[str, str]],
) -> list[tuple[str, str, str]]:
    """Insert alerts, return (kind, dataset, detail) for the digest."""
    alerts: list[tuple[str, str, str]] = []
    for check_id, dataset in error_fails:
        alerts.append(("error_fail", dataset, f"check {check_id} failed (severity error)"))
    for dataset, score in dataset_scores.items():
        mean = trailing_mean(con, "dataset", dataset)
        if mean is not None and mean - score > DROP_POINTS:
            alerts.append(
                ("score_drop", dataset, f"score {score:.1f} > {DROP_POINTS:.0f}pts below trailing mean {mean:.1f}")
            )
    for kind, dataset, detail in alerts:
        con.execute("INSERT INTO dq.alerts VALUES (?, ?, ?, ?)", [run_id, kind, dataset, detail])
    return alerts
