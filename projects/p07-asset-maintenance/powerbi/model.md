# P07 Power BI model (synthetic)

Source: gold tables in `data/warehouse.duckdb` (or `data/gold/*.parquet`
extracts), loaded via `queries/*.pq`. Set the `GoldFolder` parameter to
the absolute `data/gold` path before refresh.

## Tables and columns used

| Table | Grain | Key columns used |
|---|---|---|
| fct_work_order | WO | wo_id, asset_id, building_id, wo_type, priority, plan_category, status, raised_ts, completed_ts, trade, contractor, labour_hours, cost_gbp, days_to_complete, is_open |
| dim_asset | asset | asset_id, building_id, asset_type, install_date, expected_life_years, condition_grade, criticality, replacement_cost_gbp |
| mart_asset_health | asset | asset_id, building_id, asset_type, condition_grade, criticality, age_years, remaining_life_pct, replacement_cost_gbp, reactive_12m, is_repeat_failure, risk_score |
| dim_building | building | building_id, building_name, campus, gia_m2, primary_use |
| dim_date | day | date_day, year, month, term, teaching_week |
| dim_trade | trade | trade_id, trade |
| task_templates (CSV) | template | template_id, asset_type, frequency_months, trade, template_name | — from `projects/p07-asset-maintenance/templates/task_templates.csv` |
| rlsusers (CSV) | user | principal (email), building_id — mapping table for RLS, see below |

Hidden: `wo_id`, `space_id`, `meter_id` internals, `contractor` (drill-through
detail only), template `source_note` (keep visible in tooltip).
Date table: `dim_date[date_day]`; mark as date table.

## Relationships (single direction, many-to-one)

- fct_work_order[building_id] → dim_building[building_id]
- fct_work_order[asset_id] → dim_asset[asset_id]
- fct_work_order[trade] → dim_trade[trade] (add mapping col; same name)
- fct_work_order[raised_ts] → dim_date[date_day] (via date column)
- mart_asset_health[building_id] → dim_building[building_id]
- dim_asset[asset_id] → mart_asset_health[asset_id]

All filters flow dims → facts.

## Row-level security (REQUIRED for P07)

- Role `building_manager`: DAX filter on `dim_building`:
  `[building_id] IN CALCULATETABLE ( VALUES ( rlsusers[building_id] ), rlsusers[principal] = USERPRINCIPALNAME() )`
- Role `estates_analyst`: no filter (read-only all).
- `rlsusers` maps each manager's AAD principal to their building_id(s).
- **Test cases ("View as")** — see build-guide §3:
  1. View as building_manager (B003 manager): all tables/cards show B003
     only; totals tie to `validation/v01` filtered to B003.
  2. View as estates_analyst: all 8 buildings visible.
  3. Manager with no mapping row: blank report (document, do not error).
  4. Confirm RLS applies to mart_asset_health via the dim_building path
     (no direct filter on the mart) — test a D-grade asset table stays
     building-scoped.
