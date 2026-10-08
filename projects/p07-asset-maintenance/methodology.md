# P07 methodology — asset & maintenance KPIs

> **Synthetic data for portfolio demonstration.** Definitions below are
> SMG/CAFM-style conventions; thresholds are illustrative config, not
> industry standards. SLA targets and repeat-failure thresholds would be
> confirmed with the estates team before real use.

## Grain and window

- `fct_work_order`: one row per work order (WO). `wo_type` ∈ {PPM,
  Reactive, Statutory, Project}; `plan_category` ∈ {planned,
  other_planned, unplanned}; `days_to_complete` = completed − raised
  (days, may be 0). Small-profile window: 2026-01-01 – 2026-03-31.
- `mart_asset_health`: one row per asset; carries `reactive_12m`,
  `is_repeat_failure`, `remaining_life_pct`, `risk_score`.
- Backlog = `is_open = TRUE` as of the window end (2026-03-31);
  age = as-of date − `raised_ts`.

## KPI definitions

1. **PPM completion %** = PPM WOs completed / PPM WOs raised.
2. **Planned : reactive ratio** = (planned + other_planned) / unplanned
   (reactive only = `wo_type='Reactive'` as the unplanned anchor; the
   ratio uses plan_category for plannedness and wo_type for the
   reactive denominator — both filters documented in `v01`).
3. **Backlog age bands** = 0–30 / 31–90 / 91–180 / 180+ days since raised.
4. **SLA met % by priority** — target days config: P1 1, P2 5, P3 10,
   P4 20. *Illustrative; replace with the estate's actual SLA table.*
   Met = `days_to_complete ≤ target`.
5. **MTTR** = mean `days_to_complete` over Reactive + Complete WOs.
6. **MTBF** = mean gap between consecutive reactive completions per
   asset; assets with ≥ 2 reactive completions only.
7. **Repeat-failure assets** = ≥ 3 reactive jobs in 12 months
   (`mart_asset_health.is_repeat_failure`).
8. **Cost per m²** = WO cost / building GIA (synthetic building GIA;
   the measured value ~£0.025/m² is an artefact of the small-window
   cost window vs whole-asset GIA — flagged in findings).
9. **Cost by trade** = WO cost grouped by trade.
10. **Condition profile** = count of assets per condition grade A–D.
11. **Remaining life %** = 1 − age/expected life (`mart_asset_health`;
    may be negative for over-life assets — reported, not clamped).
12. **5-year renewal forecast** = Σ `replacement_cost_gbp` grouped by
    install year + expected life, window 2026–2030.
13. **Criticality × condition risk** = criticality (1–5) × condition
    weight (A=1..D=4): ≥16 High, ≥9 Medium, else Low.

## Task templates

`templates/task_templates.csv`: generic SFG20-*style* templates mapped
to `asset_type`. **Not SFG20 content** — commercial licence required
for the real schedule; this file only demonstrates the linkage pattern.

## Limitations

- No fault-code column: the "Pareto of fault codes" defaults to
  trade / asset type with a note in findings and the wireframe.
- One quarter of WOs — 12-month metrics (MTBF window, repeat-failure)
  use the trailing window available and are labelled.
- B012 boiler and 2025-Q4 PPM drop plants exist only in the default
  profile; see findings.md.
