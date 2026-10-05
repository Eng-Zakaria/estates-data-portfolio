# PLAN: P08 Net zero & carbon

## Goal
Carbon reporting layer on P04 gold marts: scopes, intensity, pathway variance,
baseload analysis + full Power BI handoff. No `.pbix` (protocol).

## Why P08 now
P03 is in flight (other session), P02 needs its DQ checkpoint + Docker stack.
P08 is dependency-ready (gold marts + DESNZ seed all green) and collision-free
(new `projects/p08-net-zero-carbon/` tree; will not touch `platform/dbt/`).

## Key facts (measured 2026-10-05, small profile seed 42)
- 8 buildings (B001–B008); Q1 2026 only (Jan–Mar); 1,440 daily rows
  (608,620 kWh elec / 258,739 kWh gas); `mart_carbon_monthly` 6 rows,
  baselines NULL (base year 2024 absent).
- B007 exists (Office, gas). **B019 absent** in small profile; **no summer
  months** in window → planted finding #2 only verifiable on default profile.
  Findings doc will state this honestly with exact default-profile filters.

## Tasks
1. `src/carbon.py`: pure functions — scope/fuel map, kwh→kgCO2e, intensity
   per GIA, HDD-normalised gas, linear pathway (base/end year, shape) +
   variance, overnight baseload % (00:00–05:00 min vs daily peak), rolling 12m.
2. `tests/`: hand-checked fixtures per function (1 meter × 1 month → kgCO2e
   per acceptance; pathway variance; intensity; baseload %).
3. `validation/*.sql`: headline-KPI SQL on gold marts (pathway, intensity
   league, baseload rank, summer-heating check) — doubles as PBI validation.
4. `methodology.md`: GHG Protocol Corporate Standard scopes (cite
   https://ghgprotocol.org/corporate-standard + Scope 2 Guidance
   https://ghgprotocol.org/scope-2-guidance); boundaries, exclusions,
   DESNZ single-year limitation, market-based placeholder rule.
5. `powerbi/`: model.md, queries/*.pq (folder-parameterised), measures.dax
   (commented), wireframe.md (5 pages), theme.json, build-guide.md +
   validation checklist, README.md (question→insight→decision), screenshots/.
6. `docs/findings.md`: B007 baseload measured on small profile; B019/summer
   filters specified for default profile with honest presence note.
7. `streamlit_app.py` mirror (gold tables via DuckDB, synthetic footer).
8. `README.md` (9-section template), `SPEC.md` (spec copy), Makefile target
   `p08-run` (tests) — root Makefile addition.
9. DATA.md (GHG Protocol entries), STATUS.md P08, commit.

## Risks
- HDD normalisation with only Q1 data: weak signal; methodology states limits.
- Rolling-12m on 3 months: define as trailing average with documented window.
- `warehouse.duckdb` lock contention with concurrent session → use read_only
  connections; retry once.

## Open questions
- Default-profile building count (B019?) and summer months — verify when
  default data exists; findings doc records assumption meanwhile.
