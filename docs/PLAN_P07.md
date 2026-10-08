# PLAN_P07 - Asset & maintenance performance

## Tasks
1. Spec copy (`projects/p07-asset-maintenance/SPEC.md`).
2. `src/kpis.py` pure functions: ppm_completion, planned_reactive_ratio,
   age_band (backlog), sla_met, mttr, mtbf, repeat_failure,
   remaining_life_pct, renewal_year, cost_per_m2, criticality_condition_band.
3. `tests/test_kpis.py` hand fixtures: MTTR, backlog age bands, renewal
   forecast + SLA/MTBF/PPM boundary cases.
4. `validation/v01..v06.sql` reproducing every headline KPI (run on
   `data/warehouse.duckdb`, same pattern as P06/P08).
5. `templates/task_templates.csv`: synthetic SFG20-style generic library,
   labelled "not SFG20 content", mapped to asset_type.
6. Power BI handoff: model.md (incl. RLS role DAX), measures.dax,
   wireframe.md (5 pages), theme.json, build-guide.md (incl. RLS
   "View as" test cases), queries/*.pq, README.
7. `streamlit_app.py` mirror.
8. `docs/findings.md`: bad-actors top-10 measured list; note that the
   planted B012 boiler and the 2025-Q4 PPM drop require the default
   profile (small profile is B001-B008, 2026-Q1) - report measured values
   like P06 did.
9. `docs/ACCEPTANCE_P07.md`, STATUS.md row, DATA.md entry for the
   synthetic config (SLA targets, task templates), Makefile `p07-run`.

## Assumptions / open questions
- SLA targets per priority are NOT in the gold schema: define an
  illustrative config (P1 24h, P2 5d, P3 10d, P4 20d) labelled
  `*_dev_placeholder*`-style "illustrative config", like P09
  frequencies. Listed in methodology.md.
- `as_of` for backlog ageing = max raised_ts / window end 2026-03-31.
- MTTR = mean days_to_complete over Reactive Complete WOs.
- MTBF = mean gap between consecutive reactive completions per asset,
  only assets with >= 2 reactive completions.
- Renewal forecast = sum replacement_cost_gbp grouped by
  install_date.year + expected_life_years, window 2026-2031.
- PPM completion drop planted for 2025-Q4 only applies at the default
  profile; small profile (Q1 2026) shows March completion 80.3% -
  reported as measured.
