"""P02 shared DAG defaults. Imported by every DAG (container/CI only, not host tests)."""

from __future__ import annotations

from datetime import timedelta

from tasks.callbacks import alert_on_failure, record_success

OWNER = "estates-data"
COMMON_TAGS = ["estates", "p02"]

DEFAULT_ARGS = {
    "owner": OWNER,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=30),
    "on_failure_callback": alert_on_failure,
    "on_success_callback": record_success,
}

MAX_ACTIVE_RUNS = 1
