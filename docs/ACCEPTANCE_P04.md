# ACCEPTANCE_P04 — dbt project evidence (small profile, seed 42, 2026-10-05)

## 1. `dbt build` green (small profile)

```
dbt build --profiles-dir platform/dbt --project-dir platform/dbt --full-refresh
Finished running 5 exposures, 1 incremental model, 4 seeds, 2 snapshots,
  20 table models, 147 data tests, 2 unit tests, 20 view models in ~15-19s.
Done. PASS=196 WARN=0 ERROR=0 SKIP=0 NO-OP=5 TOTAL=201
```

Incremental re-run (no `--full-refresh`): `PASS=188 … Completed successfully`
(`dbt test --select test_type:unit`: `PASS=2`).

Default (full-volume) profile: **not yet run** — recorded as the first P02/P05
follow-up (see `docs/OPEN_QUESTIONS.md` addition below).

## 2. Coverage (from `target/manifest.json`)

| Metric | Measured | Target |
|---|---|---|
| Models with ≥ 1 test | 41/41 (100%) | 100% |
| Columns documented | 292/292 (100%) | ≥ 90% |
| Data tests | 147 | ≥ 80 total |
| dbt unit tests | 2 (`test_kwh_to_kgco2e_math`, `test_work_order_enrichment`) | key logic |
| Singular tests | 11 (`tests/assert_*.sql`) | business rules |
| Marts with enforced contracts | 21/21 | all marts |
| Seeds / snapshots / sources / exposures | 4 / 2 / 16 / 5 | per spec |

## 3. Gold tables for P06–P10 (all exist, all contracted)

| Spec | Tables | Status |
|---|---|---|
| P06 | `dim_space, dim_building, dim_department, dim_date, fct_timetable_event, fct_space_observed_occupancy` | ✅ all in `main`, contracted |
| P07 | `fct_work_order, dim_asset, dim_building, dim_date, dim_trade, mart_asset_health` | ✅ (`dim_trade` added: 4 trades derived from work orders) |
| P08 | `fct_energy_daily, fct_meter_hh, dim_building, dim_emission_factor` (+ `hdd` in `fct_energy_daily`) | ✅ |
| P09 | `dim_inspection_type, fct_inspection, mart_compliance_status` | ✅ |
| P10 | `dim_space, dim_building, fct_energy_daily` (+ category map seed) | ✅ |

`dim_trade` and `fct_space_observed_occupancy` were missing from the first
draft and added during this build (see §5 for the orphan handling).

## 4. Row-count reconciliation (silver → marts, DuckDB counts)

| Flow | Silver / input | Mart | Δ | Explanation (all rows accounted) |
|---|---|---|---|---|
| space_register → `dim_space` | 495 | 495 | 0 | all room codes map to truth master |
| meter HH → `fct_meter_hh` | 68,119 | 67,822 | −297 | 297 defect-meter rows (`M-*-*xx`, never in register) dropped by inner join; date window uses a TZ-correct UTC cast (`AT TIME ZONE 'UTC'`) so late-evening 31-Mar readings are attributed correctly — zero date drops |
| `fct_meter_hh` → `fct_energy_daily` | 67,822 readings | 1,431 daily rows over 90 dates | n/a | aggregation grain change; `assert_no_negative_energy_daily` + date-relationship tests green |
| timetable → `fct_timetable_event` | 12,347 | 12,026 | −321 | 286 rows in P01-quarantined spaces + 36 future-date rows (2099-01-01); overlap 1 |
| sensors → `fct_sensor_15min` | 773,974 | 773,974 | 0 | LEFT JOIN register (no filter) |
| occupancy → `fct_space_observed_occupancy` | 257,452 | 248,877 | −8,575 | readings in P01-quarantined spaces conformed out |
| cafm → `fct_work_order` | 4,171 | 4,171 | 0 | |
| inspections → `fct_inspection` / `mart_compliance_status` | 40 | 40 / 40 | 0 | |

No unexplained loss: every dropped row is a planted defect class from
`data/raw/ground_truth.yaml` (defect meters, future dates, quarantined
spaces). Guard test `assert_silver_mart_reconciled` proves no fabricated
fact rows (every `fct_meter_hh` row exists in the cleaned input).

## 5. Fixes made during this build (deviations from first draft)

1. **Space-ID grain bug**: `dim_space` used silver room codes (`B…`) while
   facts use canonical truth IDs (`S-B…`) → all 12,347 timetable rows
   orphaned. Fixed via truth-master join in `int_current_space`
   (+ new `stg_truth__space`, `room_code` kept for traceability).
2. **Date orphans**: 36 future-date timetable rows + 64 out-of-window meter
   rows broke `dim_date` relationships. Facts now filter to the synthetic
   window 2026-01-01…2026-03-31 (documented, not hidden).
3. **`assert_asset_life_sane`**: referenced a non-mart column and flagged
   valid backlog (negative remaining life). Rewrote to flag only impossible
   values.
4. **Unit-test placement**: `unit_tests:` must be top-level YAML, not nested
   under `models:` — both tests were silently ignored until moved
   (verified: `test_type:unit` now selects 2). `source()` fixtures are
   unsupported with virtual Parquet sources, so tests target `ref()` inputs.
5. **sqlfluff AM04**: expanded 9 `SELECT *` passthroughs to explicit columns;
   fixed `.sqlfluff` dbt-templater config; `profiles.yml` honours
   `DBT_DUCKDB_PATH` for out-of-root runs.
6. **Timezone-correct date casts (follow-up refinement)**: meter/energy date
   casts use `AT TIME ZONE 'UTC'` so late-evening 31-Mar UTC readings are not
   misattributed to 01-Apr in positive-offset session timezones. This keeps
   64 legitimate boundary rows that a naive cast would drop; reconciliation
   above reflects the corrected counts (67,822 / 1,431).

## 6. Checks run

- `dbt build` (full-refresh + incremental) ✅ · `dbt test --select test_type:unit` ✅
- `dbt source freshness`: 1 pass + 3 warn (expected — synthetic window ended 2026-03-31; thresholds illustrative)
- `dbt docs generate` ✅ (`target/catalog.json` written)
- `sqlfluff lint models macros tests snapshots` (dbt templater) ✅ clean
- `dbt snapshot` runs inside `dbt build` ✅ (`snapshots.snap_spaces` 495, `snap_assets` 1,496)

## 7. Open questions added

- Default-profile `dbt build` runtime/memory not yet measured → first job in P02/P05.
- Upstream caveat (found by P03, 2026-10-05 — see `docs/OPEN_QUESTIONS.md` §11):
  P01 quarantines ~30% of legitimate CAFM rows (missing ISO-datetime
  candidate in `dates.py`). P04 is faithful to silver (`fct_work_order`
  4,171 → 4,171, zero dbt-layer loss) but inherits the gap until the P01
  fix + `make ingest` re-run lands, at which point this acceptance doc
  needs a refresh.
