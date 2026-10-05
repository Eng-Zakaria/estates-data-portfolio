# ADR 002: Airflow for batch orchestration (P02)

## Status

Accepted (2026-10-06).

## Context

Five batch ingest pipelines + dbt transform need scheduling, retries,
backfills, failure alerting and dataset-triggered transforms. Candidates:
Airflow, NiFi, Node-RED, cron.

## Decision

**Apache Airflow 3.3.1** (official CeleryExecutor compose + Postgres +
Mailpit sink), custom image adding the P01/P04 Python stack.

## Rationale

- DAG-as-code fits code review + the P05 CI gate (DagBag test); NiFi flows
  are XML blobs, poor for review.
- Sensors, dynamic task mapping, asset-aware scheduling and backfills are
  first-class; cron has none of these (no retries visibility, no lineage).
- Node-RED is event/flow-oriented and better suited to the P15 streaming
  use case; batch + backfill is Airflow's home turf.
- Asset outlets give the `transform_and_test` DAG true data-aware triggering.

## Consequences

- Heaviest local dependency (multi-container stack); mitigated by
  `make airflow-up/down`, pinned versions, and pure-logic unit tests that run
  without Airflow.
- Airflow cannot run on native Windows (POSIX-only); the stack runs in Linux
  containers, verified via `make airflow-up` + DagBag test in CI.
- Pools (`ingest_pool`, `dbt_pool`) are created by `make airflow-up`;
  documented in the runbook.
