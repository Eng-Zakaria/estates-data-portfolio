# Gold contract (for P04 dbt) — produced from silver, not built here

> Synthetic source. Gold marts will be built by dbt in P04; this file fixes names/grains so P06–P10 can plan.

## Staging (1:1 with silver, views)
`stg_space__register`, `stg_cafm__work_order`, `stg_meter__hh`, `stg_bms__trend`, `stg_insp__inspection`, `stg_tt__event`, `stg_sensor__reading`

## Dims
- `dim_building` (building_id, building_name, campus, gia_m2, primary_use)
- `dim_space` (space surrogate, room_code, building_id, space_category, nia_m2)
- `dim_asset` (asset_id, building_id, space_id, asset_type) — from CAFM AssetRef + truth assets in P04
- `dim_department`, `dim_meter` (meter_id, building_id, utility), `dim_date`, `dim_inspection_type`

## Facts / marts
- `fct_meter_hh` (meter_id, ts_utc) incremental, unique_key [meter_id, ts_utc]
- `fct_energy_daily`, `fct_work_order`, `fct_inspection`, `fct_timetable_event`, `fct_sensor_15min`
- `mart_space_utilisation`, `mart_asset_health`, `mart_carbon_monthly`, `mart_compliance_status`, `mart_dq_scorecard`

Contracts enforced in P04 (column names/types). Exposures for P06–P10 dashboards declared there.
