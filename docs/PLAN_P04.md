# PLAN: P04 dbt project (staging → intermediate → marts)

## Goal
Model the estate in dbt-duckdb on top of P01 silver (+ truth assets/calendar for missing registers). Honest rules apply.

## Tasks
1. Install + pin `dbt-duckdb==1.10.1` (pulls dbt-core 1.10.x: supports unit_tests + contracts) + `sqlfluff`; verify `dbt --version` and external-source + snapshot + incremental behavior empirically on small profile.
2. Scaffold `platform/dbt/`: `dbt_project.yml`, `profiles.yml` (duckdb, local `data/warehouse.duckdb`), `models/{staging,intermediate,marts}/`, `snapshots/`, `macros/`, `seeds/`, `tests/` (singular), `exposures.yml`.
3. Sources: silver parquet as **external sources** (`external: {location, file_format: parquet}`); truth assets/calendar/buildings as `truth` external sources (documented: no asset register in silver). Seeds: category map (from platform/refs), academic calendar (dumped from truth), DESNZ factors via download script (never hard-coded; placeholder + OPEN_QUESTIONS on failure).
4. Staging views 1:1 renames; intermediate (current space, cleaned HH, enriched WOs, asset age/life); dims + facts + 5 analysis marts per spec §Model layers.
5. `fct_meter_hh` incremental (`unique_key [meter_id, ts_utc]`, lookback window for late data); SCD2 snapshots (check strategy) on spaces/assets.
6. Macros: `kwh_to_kgco2e`, `uk_local_ts`, `is_working_hours`, `safe_divide`.
7. Tests ≥80: generic (unique/not_null/accepted_values/relationships) on every model + singular business-rule SQL + 2 dbt unit_tests. Contracts enforced on marts. Exposures for P06–P10.
8. `sqlfluff` config + lint clean; `dbt docs generate`; silver→mart reconciliation note.
9. Makefile `dbt-build/test/docs` targets; `platform/dbt/README.md` (9 sections); `docs/ACCEPTANCE_P04.md`; STATUS P04; DATA.md DESNZ entry.

## Risks
- dbt-duckdb external-source syntax from memory → verify by running on first source before mass rollout.
- DESNZ workbook URL drift → webfetch gov.uk page, script with clear error + placeholder fallback.
- No dbt_utils/dbt-expectations packages (avoid network `dbt deps`); use built-in generics + singular tests — allowed as "or equivalent".
- Snapshot + incremental on DuckDB: verify full-refresh + incremental re-run locally.

## Open questions
- Gold consumed by P06–P10 via `data/warehouse.duckdb` + Parquet extracts to `data/gold/` (for Power BI handoff).
