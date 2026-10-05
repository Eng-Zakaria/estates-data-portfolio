"""P02 Airflow callbacks: ops.pipeline_runs + Mailpit alert. Imported by DAGs only."""

from __future__ import annotations

import time

from tasks.pipeline import record_run, send_alert


def _ctx_get(context, *names, default=None):
    for name in names:
        if name in context:
            return context[name]
    return default


def record_success(context) -> None:
    dag = _ctx_get(context, "dag")
    ti = _ctx_get(context, "task_instance")
    record_run(
        {
            "dag_id": dag.dag_id if dag else "?",
            "task_id": ti.task_id if ti else "?",
            "run_id": _ctx_get(context, "run_id"),
            "data_interval_start": str(_ctx_get(context, "data_interval_start")),
            "status": "success",
            "duration_s": round(time.monotonic() - _ctx_get(context, "_p02_t0", time.monotonic()), 2),
            "rows_in": None,
            "rows_out": None,
            "error": None,
        }
    )


def alert_on_failure(context) -> None:
    dag = _ctx_get(context, "dag")
    ti = _ctx_get(context, "task_instance")
    dag_id = dag.dag_id if dag else "?"
    task_id = ti.task_id if ti else "?"
    err = _ctx_get(context, "exception", default="")
    record_run(
        {
            "dag_id": dag_id,
            "task_id": task_id,
            "run_id": _ctx_get(context, "run_id"),
            "data_interval_start": str(_ctx_get(context, "data_interval_start")),
            "status": "failed",
            "duration_s": None,
            "rows_in": None,
            "rows_out": None,
            "error": str(err)[:2000],
        }
    )
    send_alert(
        f"{dag_id}.{task_id} FAILED",
        f"dag={dag_id}\ntask={task_id}\nrun={_ctx_get(context, 'run_id')}\n"
        f"interval={_ctx_get(context, 'data_interval_start')}\nerror={err}\n"
        "See runbook: platform/orchestration/docs/runbook.md",
    )
