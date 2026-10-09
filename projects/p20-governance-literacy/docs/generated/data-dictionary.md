<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). CI fails if this page is stale. -->

# Data dictionary (generated)

Every table and column the analytics layer exposes.

Built from the dbt project at `platform/dbt/models` (yaml+sql read, 45 models, 311 columns, 45 tables). Column descriptions come from the YAML in the dbt project, so they are only as good as the descriptions written there.

| Layer | Models | Columns |
|---|---|---|
| Intermediate (joined and deduplicated) | 4 | 41 |
| Marts (dimensions, facts and analysis tables the dashboards read) | 21 | 155 |
| Seeds (reference data committed to the repository) | 4 | 19 |
| Staging (one model per source, renamed and typed) | 16 | 96 |

## Intermediate (joined and deduplicated)

### `int_asset_age`

Asset age and remaining-life share (safe division). Synthetic.

Reads: `stg_truth__asset`

| Column | Type | Description | Tests |
|---|---|---|---|
| asset_id | - | Asset id | not_null, unique |
| building_id | - | Building id | - |
| space_id | - | Space id | - |
| asset_type | - | Asset type | - |
| install_date | - | Install date | - |
| expected_life_years | - | Expected life | - |
| age_years | - | Age years | - |
| condition_grade | - | Condition | - |
| criticality | - | Criticality | - |
| replacement_cost_gbp | - | Replacement cost | - |
| remaining_life_pct | - | Remaining life share (null when life is zero) | - |

### `int_current_space`

Current space view (silver register conformed to canonical S-... space_id via truth master + building attributes). Rows whose room_code was quarantined in P01 are excluded here and counted in reconciliation. Synthetic.

Reads: `stg_space__register`, `stg_truth__building`, `stg_truth__space`

| Column | Type | Description | Tests |
|---|---|---|---|
| space_id | - | Canonical space id S-... | not_null, unique |
| room_code | - | Room code B-... as recorded | not_null, unique |
| building_id | - | Building id | not_null, relationships |
| space_category | - | Category | - |
| nia_m2 | - | NIA m2 | - |
| capacity_seats | - | Capacity | - |
| building_name | - | Building name | - |
| campus | - | Campus | - |
| gia_m2 | - | Building GIA m2 | - |

### `int_meter_hh_cleaned`

Cleaned half-hourly meter readings (union of suppliers) with local time + working-hours flag. Synthetic.

Reads: `stg_meter__hh_a`, `stg_meter__hh_b`

| Column | Type | Description | Tests |
|---|---|---|---|
| meter_id | - | Meter id | not_null |
| ts_utc | - | Timestamp UTC | not_null |
| value_kwh | - | Interval kWh | - |
| ts_local | - | London local timestamp | - |
| is_working_hours | - | Mon-Fri 09-18 London flag | - |

### `int_work_order_enriched`

Enriched work orders (chronology, cost bands, plan category). Synthetic.

Reads: `stg_cafm__work_order`

| Column | Type | Description | Tests |
|---|---|---|---|
| wo_id | - | Work order id | not_null, unique |
| asset_id | - | Asset id | not_null |
| space_id | - | Space id | - |
| building_id | - | Building id | - |
| wo_type | - | Order type | - |
| priority | - | Priority | - |
| raised_ts | - | Raised UTC | - |
| completed_ts | - | Completed UTC | - |
| status | - | Status | - |
| trade | - | Trade | - |
| contractor | - | Contractor | - |
| labour_hours | - | Labour hours | - |
| cost_gbp | - | Cost GBP | - |
| days_to_complete | - | Days raised to completed | - |
| is_open | - | Still open flag | - |
| plan_category | - | Planned/unplanned/other | - |

## Marts (dimensions, facts and analysis tables the dashboards read)

### `dim_asset`

Asset dimension from synthetic truth register.

Reads: `stg_truth__asset`

| Column | Type | Description | Tests |
|---|---|---|---|
| asset_id | varchar | Asset id | not_null, unique |
| building_id | varchar | Building id | relationships |
| space_id | varchar | Space id | - |
| asset_type | varchar | Asset type | - |
| install_date | date | Install date | - |
| expected_life_years | bigint | Expected life | - |
| condition_grade | varchar | Condition | accepted_values |
| criticality | bigint | Criticality 1-5 | - |
| replacement_cost_gbp | double | Replacement cost | - |

### `dim_building`

Building dimension from synthetic truth.

Reads: `stg_truth__building`

| Column | Type | Description | Tests |
|---|---|---|---|
| building_id | varchar | Building id | not_null, unique |
| building_name | varchar | Anonymised name | - |
| campus | varchar | Campus | - |
| gia_m2 | double | GIA m2 | - |
| nia_m2 | double | NIA m2 | - |
| n_floors | bigint | Floors | - |
| year_built | bigint | Year built | - |
| primary_use | varchar | Primary use | - |
| heating_fuel | varchar | Heating fuel | - |
| epc_band | varchar | EPC band | - |

### `dim_date`

Date dimension from academic calendar seed.

Reads: `seed_academic_calendar`

| Column | Type | Description | Tests |
|---|---|---|---|
| date_day | date | Date | not_null, unique |
| full_date | date | Date copy | - |
| year | bigint | Year | - |
| month | bigint | Month | - |
| day_of_week | bigint | ISO day of week | - |
| term | varchar | Term | - |
| teaching_week | integer | Teaching week | - |
| is_holiday | boolean | Holiday | - |
| is_weekend | boolean | Weekend | - |

### `dim_department`

Department dimension (synthetic FTE).

Reads: `stg_truth__department`

| Column | Type | Description | Tests |
|---|---|---|---|
| department_id | varchar | Department id | not_null, unique |
| department_name | varchar | Name | - |
| faculty | varchar | Faculty | - |
| staff_fte | double | Staff FTE | - |
| student_fte | double | Student FTE | - |

### `dim_emission_factor`

DESNZ 2025 GHG factors (fetched, OGL v3.0).

Reads: `seed_emission_factors`

| Column | Type | Description | Tests |
|---|---|---|---|
| fuel | varchar | Fuel key | not_null |
| scope | varchar | Scope | not_null |
| unit | varchar | kWh | - |
| factor_kgco2e_per_kwh | double | Factor | not_null |
| factor_year | integer | Year | - |
| source_url | varchar | Source URL | - |

### `dim_inspection_type`

Inspection types (frequencies illustrative, not legal duties).

Reads: `stg_truth__inspection_type`

| Column | Type | Description | Tests |
|---|---|---|---|
| inspection_type_id | varchar | Type id | not_null, unique |
| inspection_name | varchar | Name | - |
| frequency_months | bigint | Illustrative months | - |
| applies_to_asset_type | varchar | Applies to | - |

### `dim_meter`

Meter register dimension (synthetic MPAN/MPRN).

Reads: `stg_truth__meter`

| Column | Type | Description | Tests |
|---|---|---|---|
| meter_id | varchar | Meter id | not_null, unique |
| building_id | varchar | Building id | relationships |
| utility | varchar | Utility | accepted_values |
| meter_role | varchar | Main/sub | - |
| parent_meter_id | varchar | Parent meter | - |
| unit | varchar | Unit | - |

### `dim_space`

Space dimension (current register view, canonical S-... grain).

Reads: `int_current_space`

| Column | Type | Description | Tests |
|---|---|---|---|
| space_id | varchar | Canonical space id S-... | not_null, unique |
| room_code | varchar | Room code B-... as recorded | - |
| building_id | varchar | Building id | relationships |
| space_category | varchar | Category | accepted_values |
| nia_m2 | double | NIA m2 | - |
| capacity_seats | bigint | Capacity | - |
| building_name | varchar | Building name | - |
| campus | varchar | Campus | - |
| gia_m2 | double | Building GIA | - |

### `dim_trade`

Trade dimension derived from work-order trade names (synthetic).

Reads: `int_work_order_enriched`

| Column | Type | Description | Tests |
|---|---|---|---|
| trade_id | varchar | Trade slug | not_null, unique |
| trade | varchar | Trade name | - |

### `fct_energy_daily`

Daily energy by meter with degree days. Synthetic.

Reads: `fct_meter_hh`, `stg_truth__weather`

| Column | Type | Description | Tests |
|---|---|---|---|
| meter_id | varchar | Meter id | not_null |
| building_id | varchar | Building id | - |
| utility | varchar | Utility | - |
| energy_date | date | Date | relationships |
| kwh | double | Daily kWh | - |
| peak_half_hour_kwh | double | Peak HH kWh | - |
| n_periods | bigint | Period count | - |
| hdd | double | Heating degree days | - |

### `fct_inspection`

Inspection facts with type frequency. Synthetic.

Reads: `stg_insp__inspection`, `stg_truth__inspection_type`

| Column | Type | Description | Tests |
|---|---|---|---|
| inspection_id | varchar | Inspection id | not_null, unique |
| building_id | varchar | Building id | relationships |
| inspection_type_id | varchar | Type | relationships |
| frequency_months | bigint | Illustrative frequency | - |
| due_date | date | Due date | - |
| completed_date | date | Completed date | - |
| result | varchar | Result | accepted_values |

### `fct_meter_hh`

Half-hourly meter facts, incremental on (meter_id, ts_utc) with 7-day lookback. Synthetic.

 materialised as `incremental`.

Reads: `int_meter_hh_cleaned`, `stg_truth__meter`

| Column | Type | Description | Tests |
|---|---|---|---|
| meter_id | varchar | Meter id | not_null, relationships |
| ts_utc | timestamp with time zone | Timestamp UTC | not_null |
| value_kwh | double | kWh | - |
| utility | varchar | Utility | - |
| building_id | varchar | Building id | relationships |

### `fct_sensor_15min`

Sensor 15-min facts with space context. Synthetic counts only.

Reads: `stg_sensor__reading`, `stg_truth__sensor`

| Column | Type | Description | Tests |
|---|---|---|---|
| sensor_id | varchar | Sensor id | not_null |
| space_id | varchar | Space id | - |
| sensor_type | varchar | Type | accepted_values |
| ts_utc | timestamp with time zone | Timestamp UTC | not_null |
| value | double | Value | - |

### `fct_space_observed_occupancy`

Observed occupancy counts per space from occupancy_count sensors (P06 no-show analysis). Synthetic counts only, no personal data.

Reads: `int_current_space`, `stg_sensor__reading`, `stg_truth__sensor`

| Column | Type | Description | Tests |
|---|---|---|---|
| sensor_id | varchar | Sensor id | not_null |
| space_id | varchar | Space id | not_null, relationships |
| ts_utc | timestamp with time zone | Timestamp UTC | not_null |
| observed_count | double | Observed headcount | - |

### `fct_timetable_event`

Timetable event facts with durations. Synthetic.

Reads: `int_current_space`, `stg_tt__event`

| Column | Type | Description | Tests |
|---|---|---|---|
| event_id | varchar | Event id | not_null, unique |
| space_id | varchar | Space id | relationships |
| event_date | date | Date | relationships |
| start_time | varchar | Start HH:MM | - |
| end_time | varchar | End HH:MM | - |
| module_code | varchar | Module | - |
| group_size | integer | Group size | - |
| duration_hours | double | Duration hours | - |

### `fct_work_order`

Work order facts (enriched chronology and cost). Synthetic.

Reads: `int_work_order_enriched`

| Column | Type | Description | Tests |
|---|---|---|---|
| wo_id | varchar | Work order id | not_null, unique |
| asset_id | varchar | Asset id | relationships |
| space_id | varchar | Space id | - |
| building_id | varchar | Building id | - |
| wo_type | varchar | Type | accepted_values |
| priority | varchar | Priority | accepted_values |
| raised_ts | timestamp with time zone | Raised UTC | - |
| completed_ts | timestamp with time zone | Completed UTC | - |
| status | varchar | Status | - |
| trade | varchar | Trade | - |
| contractor | varchar | Contractor | - |
| labour_hours | double | Hours | - |
| cost_gbp | double | Cost | - |
| days_to_complete | bigint | Days to complete | - |
| is_open | boolean | Open flag | - |
| plan_category | varchar | Planned/unplanned | - |

### `mart_asset_health`

Asset health mart (age, repeats, risk). Synthetic.

Reads: `fct_work_order`, `int_asset_age`

| Column | Type | Description | Tests |
|---|---|---|---|
| asset_id | varchar | Asset id | not_null, unique, relationships |
| building_id | varchar | Building id | - |
| asset_type | varchar | Type | - |
| condition_grade | varchar | Condition | - |
| criticality | bigint | Criticality | - |
| age_years | bigint | Age | - |
| remaining_life_pct | double | Remaining share | - |
| replacement_cost_gbp | double | Replacement cost | - |
| reactive_12m | bigint | Reactive count | - |
| is_repeat_failure | boolean | Repeat flag | - |
| risk_score | bigint | Criticality x condition weight | - |

### `mart_carbon_monthly`

Monthly carbon by fuel with baseline variance (baseline null when base year absent). Synthetic energy, DESNZ 2025 factors.

Reads: `dim_emission_factor`, `fct_energy_daily`

| Column | Type | Description | Tests |
|---|---|---|---|
| month | date | Month | - |
| fuel | varchar | Fuel key | - |
| kwh | double | Monthly kWh | - |
| kgco2e | double | kgCO2e | - |
| baseline_kwh | double | Base-year same-fuel average (null if absent) | - |
| variance_to_baseline | double | (kwh-baseline)/baseline | - |

### `mart_compliance_status`

Compliance status mart (single status logic). Synthetic, illustrative frequencies.

Reads: `fct_inspection`

| Column | Type | Description | Tests |
|---|---|---|---|
| inspection_id | varchar | Inspection id | not_null, unique |
| building_id | varchar | Building id | - |
| inspection_type_id | varchar | Type | - |
| due_date | date | Due | - |
| completed_date | date | Completed | - |
| result | varchar | Result | - |
| status | varchar | Status | accepted_values |
| days_overdue | bigint | Days overdue | - |
| risk_score | integer | Risk 0-4 | - |

### `mart_dq_scorecard`

DQ scorecard snapshot from P01 reconciliation rates. Synthetic.

Reads: `seed_dq_snapshot`

| Column | Type | Description | Tests |
|---|---|---|---|
| dataset | varchar | Dataset | not_null, unique |
| grain | varchar | Grain | - |
| rows_checked | integer | Rows checked | - |
| rows_quarantined | integer | Rows quarantined | - |
| pass_rate | double | Pass rate | - |

### `mart_space_utilisation`

Space utilisation analysis mart (frequency and occupancy proxies). Synthetic.

Reads: `dim_date`, `dim_space`, `fct_timetable_event`

| Column | Type | Description | Tests |
|---|---|---|---|
| space_id | varchar | Space id | not_null, unique, relationships |
| building_id | varchar | Building id | - |
| space_category | varchar | Category | - |
| nia_m2 | double | NIA | - |
| capacity_seats | bigint | Capacity | - |
| n_events | bigint | Event count | - |
| booked_hours | double | Booked hours | - |
| available_hours | double | Available hours | - |
| frequency_rate | double | Booked/available | - |
| occupancy_rate | double | Avg group/capacity | - |
| avg_group_size | double | Avg group | - |

## Seeds (reference data committed to the repository)

### `seed_academic_calendar`

Academic calendar from synthetic truth (terms, teaching weeks, holidays).

 materialised as `seed`.

| Column | Type | Description | Tests |
|---|---|---|---|
| date | - | Date | not_null, unique |
| term | - | Term | - |
| teaching_week | - | Teaching week number | - |
| is_holiday | - | Holiday flag | - |
| is_weekend | - | Weekend flag | - |

### `seed_dq_snapshot`

DQ scorecard snapshot from P01 reconciliation (scripts/build_dq_seed.py). Synthetic.

 materialised as `seed`.

| Column | Type | Description | Tests |
|---|---|---|---|
| dataset | - | Source dataset | not_null, unique |
| grain | - | row or cell grain | - |
| rows_checked | - | Rows checked | - |
| rows_quarantined | - | Rows quarantined | - |
| pass_rate | - | 1 - quarantined/checked | - |

### `seed_emission_factors`

DESNZ 2025 GHG conversion factors (fetched by scripts/fetch_desnz.py, OGL v3.0). Never hard-coded.

 materialised as `seed`.

| Column | Type | Description | Tests |
|---|---|---|---|
| fuel | - | natural_gas or electricity | not_null |
| scope | - | GHG Protocol scope | not_null |
| unit | - | kWh | - |
| factor_kgco2e_per_kwh | - | kgCO2e per kWh | not_null |
| year | - | Factor year | not_null |
| source_url | - | Source workbook URL | - |

### `seed_space_category_map`

Space category raw-to-canonical map (v1, from platform/refs). Synthetic mapping.

 materialised as `seed`.

| Column | Type | Description | Tests |
|---|---|---|---|
| raw_category | - | Raw recorded spelling | not_null |
| return_category | - | Canonical category | not_null |
| map_version | - | Map version | - |

## Staging (one model per source, renamed and typed)

### `stg_bms__trend`

BMS trend readings staging (long). Synthetic.

Reads: `silver.bms_trends`

| Column | Type | Description | Tests |
|---|---|---|---|
| point_id | - | Point id with unit in name | not_null |
| ts_utc | - | Timestamp UTC | not_null |
| value | - | Reading value | - |

### `stg_cafm__work_order`

CAFM work orders staging. Synthetic.

Reads: `silver.cafm_workorders`

| Column | Type | Description | Tests |
|---|---|---|---|
| wo_id | - | Work order id | not_null, unique |
| asset_id | - | Asset reference | not_null |
| space_id | - | Space id | - |
| building_id | - | Building id | - |
| wo_type | - | Order type | accepted_values |
| priority | - | Priority | accepted_values |
| raised_ts | - | Raised timestamp UTC | not_null |
| completed_ts | - | Completed timestamp UTC | - |
| status | - | Normalised status | - |
| trade | - | Trade | - |
| contractor | - | Contractor | - |
| labour_hours | - | Labour hours | - |
| cost_gbp | - | Cost GBP | - |

### `stg_insp__inspection`

Statutory inspections staging. Synthetic; frequencies illustrative.

Reads: `silver.statutory_inspections`

| Column | Type | Description | Tests |
|---|---|---|---|
| inspection_id | - | Inspection id | not_null, unique |
| building_id | - | Building id | not_null |
| inspection_type_id | - | Inspection type | not_null |
| due_date | - | Due date | not_null |
| completed_date | - | Completed date | - |
| result | - | Pass/Fail/Advisory | - |

### `stg_meter__hh_a`

Supplier A half-hourly readings staging. Synthetic.

Reads: `silver.meter_hh_supplierA`

| Column | Type | Description | Tests |
|---|---|---|---|
| meter_id | - | Meter id | not_null |
| ts_utc | - | Timestamp UTC | not_null |
| value_kwh | - | Interval kWh | - |
| unit | - | Unit | - |
| quality_flag | - | Quality flag | - |

### `stg_meter__hh_b`

Supplier B half-hourly readings staging (reshaped long in silver). Synthetic.

Reads: `silver.meter_hh_supplierB`

| Column | Type | Description | Tests |
|---|---|---|---|
| meter_id | - | Meter id | not_null |
| ts_utc | - | Timestamp UTC | not_null |
| value_kwh | - | Interval kWh | - |
| unit | - | Unit | - |
| quality_flag | - | Quality flag | - |

### `stg_sensor__reading`

Sensor 15-min readings staging. Synthetic counts only, no personal data.

Reads: `silver.sensors`

| Column | Type | Description | Tests |
|---|---|---|---|
| sensor_id | - | Sensor id | not_null |
| ts_utc | - | Timestamp UTC | not_null |
| value | - | Reading value | - |

### `stg_space__register`

Space register staging (1:1 rename of silver). Synthetic.

Reads: `silver.space_register`

| Column | Type | Description | Tests |
|---|---|---|---|
| room_code | - | Room code | not_null, unique |
| building_id | - | Canonical building id | not_null |
| building_name | - | Building name as recorded | - |
| space_category | - | Conformed category | accepted_values |
| nia_m2 | - | Net internal area m2 | - |
| capacity_seats | - | Seat capacity | - |

### `stg_truth__asset`

Asset register from synthetic truth (no asset source in silver). Synthetic.

Reads: `truth.assets`

| Column | Type | Description | Tests |
|---|---|---|---|
| asset_id | - | Asset id | not_null, unique |
| building_id | - | Building id | not_null |
| space_id | - | Space id | not_null |
| asset_type | - | Asset type | - |
| install_date | - | Install date | - |
| expected_life_years | - | Expected life years | - |
| condition_grade | - | Condition A-D | accepted_values |
| criticality | - | Criticality 1-5 | - |
| replacement_cost_gbp | - | Replacement cost GBP | - |

### `stg_truth__building`

Buildings from synthetic truth. Synthetic.

Reads: `truth.buildings`

| Column | Type | Description | Tests |
|---|---|---|---|
| building_id | - | Building id | not_null, unique |
| building_name | - | Anonymised name | - |
| campus | - | Campus | - |
| gia_m2 | - | Gross internal area m2 | - |
| nia_m2 | - | Net internal area m2 | - |
| n_floors | - | Floor count | - |
| year_built | - | Year built | - |
| primary_use | - | Primary use | - |
| heating_fuel | - | Heating fuel | - |
| epc_band | - | EPC band | - |

### `stg_truth__department`

Departments from synthetic truth. Synthetic FTE.

Reads: `truth.departments`

| Column | Type | Description | Tests |
|---|---|---|---|
| department_id | - | Department id | not_null, unique |
| department_name | - | Department name | - |
| faculty | - | Faculty | - |
| staff_fte | - | Staff FTE (synthetic) | - |
| student_fte | - | Student FTE (synthetic) | - |

### `stg_truth__inspection_type`

Inspection types from synthetic truth. Frequencies are illustrative config, not legal duties.

Reads: `truth.inspection_types`

| Column | Type | Description | Tests |
|---|---|---|---|
| inspection_type_id | - | Type id | not_null, unique |
| inspection_name | - | Type name | - |
| frequency_months | - | Illustrative frequency months | - |
| applies_to_asset_type | - | Applies to | - |

### `stg_truth__meter`

Meter register from synthetic truth. Synthetic MPAN/MPRN.

Reads: `truth.meters`

| Column | Type | Description | Tests |
|---|---|---|---|
| meter_id | - | Meter id | not_null, unique |
| building_id | - | Building id | not_null |
| utility | - | Utility | accepted_values |
| meter_role | - | Main/sub | - |
| parent_meter_id | - | Parent meter | - |
| unit | - | Unit | - |

### `stg_truth__sensor`

Sensor register from synthetic truth. Aggregate counts only, no personal data.

Reads: `truth.sensors`

| Column | Type | Description | Tests |
|---|---|---|---|
| sensor_id | - | Sensor id | not_null, unique |
| space_id | - | Space id | not_null |
| sensor_type | - | co2/temp/rh/occupancy_count | - |
| install_date | - | Install date | - |

### `stg_truth__space`

Space master from synthetic truth (canonical space_id S-... plus room_code B-...). Used to conform silver room codes to timetable/asset grain. Synthetic.

Reads: `truth.spaces`

| Column | Type | Description | Tests |
|---|---|---|---|
| space_id | - | Canonical space id S-... | not_null, unique |
| room_code | - | Room code B-... | not_null, unique |
| building_id | - | Building id | not_null |
| space_category | - | Truth category | - |
| capacity_seats | - | Seat capacity | - |
| nia_m2 | - | Net internal area m2 | - |

### `stg_truth__weather`

Hourly weather from synthetic truth (temp + degree-day contributions). Synthetic.

Reads: `truth.weather`

| Column | Type | Description | Tests |
|---|---|---|---|
| ts_utc | - | Timestamp UTC | not_null |
| temp_c | - | Temperature C | - |
| hdd_base15_5 | - | HDD contribution base 15.5 | - |
| cdd | - | CDD contribution | - |

### `stg_tt__event`

Timetable events staging. Synthetic.

Reads: `silver.timetable`

| Column | Type | Description | Tests |
|---|---|---|---|
| event_id | - | Event id | not_null, unique |
| space_id | - | Space id | not_null |
| event_date | - | Local date | - |
| start_time | - | Start HH:MM | - |
| end_time | - | End HH:MM | - |
| module_code | - | Module code | - |
| group_size | - | Group size | - |

All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any real university, building or estate, and nothing here is a compliance statement.
