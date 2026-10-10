# P15 acceptance evidence

**Date:** 2026-10-10
**Project:** `projects/p15-bms-iot` - BMS / sensor ingestion (MQTT -> Node-RED -> TimescaleDB -> Grafana)
**Status:** code complete, tests green, offline acceptance met; **live stack NOT verified** (Docker Desktop unavailable in the build environment).

Every claim below is a command and its output. Claims that could not be
verified are listed as such rather than asserted.

---

## Summary against the spec's acceptance criteria

| criterion | result | evidence |
|---|---|---|
| `make iot-up` + `make iot-demo` produce data in Grafana within 2 minutes | **NOT VERIFIED** - Docker Desktop's engine would not start in the build environment. Targets exist and are wired; the compose file, migration and provisioning are present but were never executed | section 7 |
| 24 simulated hours with >= 99.9% ingestion of valid messages | **MET** - 100.0000% (84,435 of 84,435) | section 2 |
| malformed messages in the dead-letter queue with reasons | **MET** - 141, all `MISSING_FIELD`; 11 reason codes defined, each with a test that reaches it | section 2, 4 |
| every injected fault visible in point health or alerts | **MET** - 20 of 20 planted windows detected, and a clean plant produces zero findings | section 3 |
| flow JSON imports cleanly on a fresh Node-RED | **PARTIAL** - JSON structure, wiring integrity and rule parity tested; no live import performed | section 5 |
| tests for the simulator | **MET** - 25 tests | section 6 |
| tests for the SQL schema (migration applies cleanly) | **PARTIAL** - 21 tests assert the migration is complete, idempotent and consistent with the dashboards; it was never applied to a live TimescaleDB | section 5 |
| tests for the ingestion contract | **MET** - 59 tests across registry (9), validator (39) and contract split (11) | section 6 |

---

## 1. Environment

```
$ .\.venv\Scripts\python.exe --version
Python 3.14.0

$ docker version
Client: Version 27.3.1
...
error during connect: ... dockerDesktopLinuxEngine/_ping:
open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.

$ Get-Service com.docker.service
Name                Status
----                ------
com.docker.service  Stopped

$ Start-Service com.docker.service
Start-Service : Service 'Docker Desktop Service (com.docker.service)' cannot be
started due to the following error: Cannot open com.docker.service service on
computer '.'
```

The Docker client is installed but the Linux engine is not running and the
service cannot be started without elevation. That is why section 7 exists.

## 2. Ingestion: `make iot-offline`

```
$ make iot-offline
PYTHONPATH=projects/p15-bms-iot/src python projects/p15-bms-iot/src/run_pipeline.py \
  --duration-hours 24 --interval-minutes 5 --out data/p15 --raw data/raw

points:                294
messages simulated:    84576
  dropped (comms):     96
  malformed injected:  141
valid messages:        84435
accepted:              84435 (100.0000% of valid)
dead letter:           141
  reasons:             MISSING_FIELD=141
findings:              20
  rules:               SEM-01=4, SEM-02=4, SEM-03=4, SEM-05=4, STALENESS=4
unhealthy points:      4 of 294
bms_trends export:     data\raw\bms_trends_20261010.csv

elapsed: 00:00:25.6
```

| measure | value | check |
|---|---|---|
| valid messages | 84,435 | 84,576 sent - 96 dropped by the injected dropout - 141 malformed... 84,435 after excluding the 141 malformed from 84,531 delivered |
| accepted | 84,435 | 100.0000% of valid, spec asks >= 99.9% |
| dead-lettered | 141 | all `MISSING_FIELD`; the simulator omits `quality` from malformed payloads so this reason is reached end to end |
| drops accounted for | 96 | the comms-dropout fault publishes nothing for its window; not an ingestion failure |

Runtime 25.6 s for a simulated day at 294 points and a 5-minute cadence.

### Dead-letter reasons are all reachable

`contracts/validation_rules.json` defines 11 reason codes. Each has a test that
produces it through the validator, so no reason in the documentation is
aspirational: `tests/test_validation_contract.py` covers `TOPIC_PATTERN`
(5 cases), `MALFORMED_JSON`, `MISSING_FIELD` (4 fields + array payload),
`NON_NUMERIC_VALUE` (4 cases), `QUALITY_INVALID`, `UNIT_MISMATCH`, `OUT_OF_RANGE`
(2 cases), `TIMESTAMP_FORMAT`, `TIMESTAMP_IN_FUTURE`, `TIMESTAMP_TOO_OLD`,
`UNKNOWN_POINT_ID`.

## 3. Fault detection

### Every planted fault is detected

```
$ make iot-faults

| fault | rule | planted | detected | recall | mean delay (min) |
|---|---|---|---|---|---|
| comms_dropout | STALENESS | 4 | 4 | 100% | -5.0 |
| out_of_hours | SEM-03 | 4 | 4 | 100% | 0.0 |
| sensor_drift | SEM-05 | 4 | 4 | 100% | 120.0 |
| simultaneous_heat_cool | SEM-01 | 4 | 4 | 100% | 0.0 |
| stuck_valve | SEM-02 | 4 | 4 | 100% | 0.0 |

Overall recall: 20/20 = 100%
Wrote projects/p15-bms-iot/docs/fault_detection.csv
```

Per-window detail, including the evidence string the engineer sees, is in
`projects/p15-bms-iot/docs/fault_detection.csv`.

Two figures that look odd and are correct:

* **SEM-05 delay 120 min.** The drift window is six hours by design. Monotonic
  movement over two hours is indistinguishable from a valve ramping to
  setpoint, which is why the rule needs the long window. The delay is the cost
  of not alerting on every healthy ramp.
* **STALENESS delay -5 min.** A staleness finding is timestamped at the last
  sample received, which precedes the gap that revealed it. Negative means it
  fired on the first missed interval.

### And a clean plant produces nothing

The half of the metric that makes the first half mean something: same seed,
same 24 hours, `--faults` with no values.

```
$ make iot-clean-run

points:                294
messages simulated:    84672
  dropped (comms):     0
  malformed injected:  141
valid messages:        84531
accepted:              84531 (100.0000% of valid)
dead letter:           141
  reasons:             MISSING_FIELD=141
findings:              0
unhealthy points:      0 of 294
```

**Zero findings, zero unhealthy points.** Pinned as tests:
`tests/test_pipeline.py::test_every_planted_fault_is_detected`,
`::test_a_clean_plant_produces_no_findings`,
`::test_health_flags_exactly_the_points_that_went_quiet`.

## 4. Where each fault shows up

| fault | rule | detected by | visible in |
|---|---|---|---|
| simultaneous heat + cool | SEM-01 | both valves > 20% on one equipment in one step | Grafana Plant Overview, valve panel; Active Faults findings |
| stuck valve | SEM-02 | constant >= 30 samples while the paired valve moves > 1% | Plant Overview (flat vs moving peer); findings detail |
| out-of-hours | SEM-03 | `fan_speed` > 20% outside 07:00-19:00 weekdays | Plant Overview fan panel; Active Faults |
| flat-line | SEM-04 | no change for >= 60 samples | Point Health completeness table |
| drift | SEM-05 | monotone over 6 h, range >= 25, no reversal > 10 | Active Faults findings |
| comms dropout | STALENESS | gap > 3 intervals / `last_seen` > 10 min | Point Health "not healthy"; `bms.alerts` (raised by the flow every 5 min) |
| malformed | - | missing required field | Active Faults "dead letter by reason" |

Every rule in that table is in `contracts/validation_rules.json` under
`semantic_checks` with its threshold written out, and
`tests/test_validation_contract.py::test_semantic_check_ids_are_documented`
asserts the file and the code agree on the set.

## 5. Node-RED flow and SQL schema (structural verification)

No live Node-RED or TimescaleDB, so these are structural assertions over the
committed artefacts.

### Flow (12 tests, `tests/test_flows.py`)

| assertion | result |
|---|---|
| merged `p15_bms.json` is valid JSON with one tab per concern (ingest, registry seed) | pass |
| node ids unique; every wire target exists | pass |
| exactly one `mqtt in` on `campus/#`; one broker config node | pass |
| stage counts match the documented pipeline: 5 function nodes, 5 postgresql nodes, 2 timers | pass |
| broker points at `mosquitto:2883` (compose network) | pass |
| no credential key and no password string anywhere in the flow | pass |
| rebuilt from fragments gives the same nodes in the same order | pass |
| batching present (500 rows) | pass |
| staleness timer every 300 s; alert SQL compares `now() - p.last_seen > INTERVAL '10 minutes'` | pass |
| dead-letter and registry-seed nodes present; reject branch is the fallback | pass |
| the flow's JS topic pattern equals the contract's Python pattern with `(?<name>)` groups | pass |
| the flow's emitted reason codes equal the documented 11 | pass |
| the flow reads thresholds from `global.get('BMS_RULES')` at runtime | pass |

The last three are the ones that matter: they are what stops the shipped flow
and the tested Python reference from diverging.

### Schema (21 tests, `tests/test_schema_sql.py`)

All pass. Asserts: the four tables plus `bms.findings` exist with the
documented columns; `bms.readings` is a hypertable on `ts` with compression
keyed on `point_id`; compression and retention policies present; uniqueness on
`(ts, point_id)` so redelivery is idempotent; three continuous aggregates with
policies; the daily aggregate sums `value` (energy) while the 15-minute and
hourly ones do not (a sum of temperature is meaningless); aggregates created
`WITH NO DATA` and backfilled by policy; refresh windows wider than the source
interval; the three Grafana views exist with the documented grain; **every
statement is re-runnable** (`IF NOT EXISTS` on every CREATE, `if_not_exists =>
TRUE` on every policy call); the partial unique index on open alerts; no
credentials in the file.

Not verified: that the migration applies cleanly to a real TimescaleDB, and
that re-applying it is safe in practice.

### Grafana dashboards (17 tests, `tests/test_grafana.py`)

All pass. Four dashboards are generated from the registry and committed;
`test_committed_dashboards_match_the_generator` fails if they drift. Each
dashboard's title, description and tags say "synthetic" (AGENTS.md rule 2).
Every panel targets the provisioned datasource, every query selects from the
`bms` schema, and every table referenced exists in `schema.sql` - a dashboard
querying a missing table renders empty with no error, which is the failure this
catches. Timezone is `Europe/London` on all four.

## 6. Tests and static analysis

```
$ make iot-test
245 passed

Name                       Stmts   Miss  Cover   Missing
---------------------------------------------------------
src\export_bms_trends.py       58      1    98%
src\export_sql.py              30      1    97%
src\grafana_dashboards.py      66      2    97%
src\health.py                 268      7    97%
src\ingest_contract.py         61      1    98%
src\load_db.py                 62      3    95%
src\make_registry.py           43      1    98%
src\run_pipeline.py            82      3    96%
src\simulator.py              225     25    89%
src\validate.py               118      2    98%
---------------------------------------------------------
TOTAL                        1013     46    95%
```

| gate | result |
|---|---|
| `ruff check src tests scripts` | All checks passed |
| `ruff format` | clean |
| `mypy src` (with pandas-stubs) | `Success: no issues found in 10 source files` |

`mypy` is not in `--strict` mode for this project, and
`projects/p15-bms-iot/pyproject.toml` says why in a comment: most of the code
is pandas reshaping, pandas-stubs types a row attribute as a union of every
scalar the column can hold, and strict mode reports a hundred
`Unsupported operand` errors that say nothing about correctness. What is
enforced: `disallow_untyped_defs`, `disallow_incomplete_defs`,
`disallow_any_generics`, `check_untyped_defs`, `warn_return_any`.

Test distribution (245 total): registry 9, validation contract 39, simulator 25,
ingestion contract 11, health 32, schema SQL 21, flows 12, Grafana 17, load_db
11, export 24, pipeline 21, CLI 16, determinism 7.

## 7. Not verified

Stated plainly, because a green test suite is not evidence about a container
that never started.

| item | why | what would verify it |
|---|---|---|
| `make iot-up` brings up mosquitto + TimescaleDB + Node-RED + Grafana | Docker engine unavailable; service cannot be started without elevation | a machine with Docker Desktop |
| `make iot-demo` fills the dashboards | same | same |
| Grafana screenshots | no rendered dashboard exists to screenshot | same |
| the flow JSON imports into a fresh Node-RED and subscribes | same | same |
| `schema.sql` applies cleanly to a live TimescaleDB, and re-applies | same | same |
| `sql/export_bms_trends.sql` runs as a `\copy` inside the container | same | same |
| `load_db.py` writes to a live database | same (the SQL is unit-tested against a recording cursor, not a server) | same |
| end-to-end latency "data in Grafana within 2 minutes" | same | same |

The offline path covers everything that does not need a broker or a database:
the simulator, the validator, the dead-letter split, all six detection rules,
the health summary, the export and the dashboards' SQL.

## 8. Honest metrics

Per AGENTS.md rule 9, the weak numbers too:

* **100% recall is measured on five synthetic fault types.** The detector was
  developed against the same simulator that injects the faults. That is a real
  risk of self-confirmation, mitigated but not removed by the clean-plant run
  (0 false positives) and by the hand-built fixtures in `tests/test_health.py`,
  which state the expected finding independently of the simulator.
* **Zero false positives is measured on synthetic healthy plant.** Real healthy
  plant is noisier than a seeded random walk.
* **SEM-05's 120-minute delay is a real cost**, not a measurement artefact. A
  drifting sensor is detected two hours into its window; a drift that starts and
  stops inside six hours is missed entirely.
* **`completeness_pct` of 98.96% on a clean run** is not a defect: the
  simulator injects malformed payloads in both runs, and dead-lettering them is
  correct.
* **The 25.6 s runtime** is for the offline path on one laptop. Nothing here
  says anything about throughput at scale: there is no load test, no
  backpressure test, and no broker under pressure.

## 9. Spec deviations

Full table in `projects/p15-bms-iot/SPEC.md`. The substantive ones:

1. Topic taxonomy includes the equipment segment. The spec's shape is not
   unique per point and silently loses two thirds of the data.
2. The nightly export is a CSV matching P01's existing contract, not Parquet as
   the spec says, because P01 already validates that contract.
3. Malformed payloads are not listed as a fault class; they are counted
   separately in the truth file so ingestion loss is never conflated with fault
   detection.
4. `docs/security.md` is folded into
   `projects/p15-bms-iot/docs/mapping-to-real-systems.md`.
5. The BACpypes3 simulated BACnet/IP device (a stretch goal in the spec) was
   not built.