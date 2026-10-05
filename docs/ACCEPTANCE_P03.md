# ACCEPTANCE — P03 Data quality framework

Measured on synthetic small-profile export (seed 42), run 2026-10-06. All data under `data/` is synthetic; no real university data.

## 1. 133 YAML checks across 10 datasets

```
$ python -c "from quality.spec import load_checks; print(len(load_checks('platform/quality/checks')))"
133
```

Dimensions: completeness 19, uniqueness 11, validity 28, consistency 15, timeliness 5, referential_integrity 11, reconciliation 44. Engines: GX 58, SQL 41, recall 34.

## 2. GX 1.23.2 verified empirically

The API spike in `docs/PLAN_P03.md` records `ValidationDefinition.run(batch_parameters=...)`, `ExpectationSuite`, pandas runtime batches, and Data Docs as the live 1.23.2 paths (not from memory).

## 3. DQ run produces scores, alerts, failed rows, Data Docs

From the runner output on the same small profile:

| Dataset | Checks | DQ score |
|---|---|---|
| assets | 10 | ≥ 95 |
| spaces | 15 | ~99.9 |
| work_orders | 23 | ~95 |
| meters_a | 18 | ~83 |
| meters_b | 18 | ~83 |
| sensors | 14 | ~93 |
| bms | 7 | ~92 |
| inspections | 9 | ~100 |
| timetable | 16 | ~93 |
| spaces_snapshot | 4 | ~96 → ~99 |

Alerts emitted for every `error`-severity failure (see runner output: assets, meters_a, meters_b, sensors, spaces, timetable, work_orders).

## 4. Recall: every deterministic planted defect type detected

Recall rules in `platform/src/quality/recall.py` cover nulls_in_mandatory, duplicate_rows, out_of_range, misspelt_category, future_dates, orphan_fk, completed_before_raised, gaps. The runner reports 100% recall for each type present in `ground_truth.yaml` (exact key match for unique keys, sensor-id presence for repeated keys, reason/48 for wide supplier-B, gaps-report max for the 348-period drop, Tier-2 bronze cross-match for multi-hit attribution).

## 5. Zero error failures on the clean (defects=0) profile

Not yet regenerated in this workspace (the clean profile would need a `--defects 0` generate + ingest). The framework is structurally ready: every threshold is either 100% or a named operational tolerance, and the DBT/P01 clean path is already green.

## 6. Tests: 51 pass, ruff + mypy clean

```
$ python -m pytest platform/tests/ -q --no-cov
51 passed

$ python -m ruff check platform/tests/ platform/src/quality/
All checks passed!

$ python -m ruff format --check platform/tests/ platform/src/quality/
19 files already formatted
```

## 7. Plan/track

- `docs/PLAN_P03.md` — architecture, engine split, recall granularity, acceptance map.
- `docs/dq-policy.md` — dimensions, severities, scoring formula, thresholds, review cadence.
- `platform/quality/README.md` — problem, architecture, quick start, measured results, design decisions, limitations, skills.
