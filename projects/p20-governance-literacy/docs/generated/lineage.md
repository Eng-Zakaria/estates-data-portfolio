<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). CI fails if this page is stale. -->

# Lineage (generated)

Where every table comes from, and what reads it.

Upstream to downstream, read from `{{ ref() }}` and `{{ source() }}` calls in the model SQL plus `exposures.yml` (yaml+sql read). 55 edges over 45 models.

```mermaid
flowchart LR
  subgraph staging["staging"]
    stg_bms__trend()
    stg_cafm__work_order()
    stg_insp__inspection()
    stg_meter__hh_a()
    stg_meter__hh_b()
    stg_sensor__reading()
    stg_space__register()
    stg_truth__asset()
    stg_truth__building()
    stg_truth__department()
    stg_truth__inspection_type()
    stg_truth__meter()
    stg_truth__sensor()
    stg_truth__space()
    stg_truth__weather()
    stg_tt__event()
  end
  subgraph intermediate["intermediate"]
    int_asset_age()
    int_current_space()
    int_meter_hh_cleaned()
    int_work_order_enriched()
  end
  subgraph marts["marts"]
    dim_asset()
    dim_building()
    dim_date()
    dim_department()
    dim_emission_factor()
    dim_inspection_type()
    dim_meter()
    dim_space()
    dim_trade()
    fct_energy_daily()
    fct_inspection()
    fct_meter_hh()
    fct_sensor_15min()
    fct_space_observed_occupancy()
    fct_timetable_event()
    fct_work_order()
    mart_asset_health()
    mart_carbon_monthly()
    mart_compliance_status()
    mart_dq_scorecard()
    mart_space_utilisation()
  end
  dim_asset --> p07_maintenance_dashboard
  dim_building --> p06_space_dashboard
  dim_building --> p10_institutional_return
  dim_date --> mart_space_utilisation
  dim_emission_factor --> mart_carbon_monthly
  dim_emission_factor --> p08_carbon_dashboard
  dim_space --> mart_space_utilisation
  dim_space --> p06_space_dashboard
  dim_space --> p10_institutional_return
  dim_trade --> p07_maintenance_dashboard
  fct_energy_daily --> mart_carbon_monthly
  fct_energy_daily --> p08_carbon_dashboard
  fct_energy_daily --> p10_institutional_return
  fct_inspection --> mart_compliance_status
  fct_inspection --> p09_compliance_dashboard
  fct_meter_hh --> fct_energy_daily
  fct_space_observed_occupancy --> p06_space_dashboard
  fct_timetable_event --> mart_space_utilisation
  fct_work_order --> mart_asset_health
  fct_work_order --> p07_maintenance_dashboard
  int_asset_age --> mart_asset_health
  int_current_space --> dim_space
  int_current_space --> fct_space_observed_occupancy
  int_current_space --> fct_timetable_event
  int_meter_hh_cleaned --> fct_meter_hh
  int_work_order_enriched --> dim_trade
  int_work_order_enriched --> fct_work_order
  mart_asset_health --> p07_maintenance_dashboard
  mart_carbon_monthly --> p08_carbon_dashboard
  mart_compliance_status --> p09_compliance_dashboard
  mart_space_utilisation --> p06_space_dashboard
  seed_academic_calendar --> dim_date
  seed_dq_snapshot --> mart_dq_scorecard
  seed_emission_factors --> dim_emission_factor
  stg_cafm__work_order --> int_work_order_enriched
  stg_insp__inspection --> fct_inspection
  stg_meter__hh_a --> int_meter_hh_cleaned
  stg_meter__hh_b --> int_meter_hh_cleaned
  stg_sensor__reading --> fct_sensor_15min
  stg_sensor__reading --> fct_space_observed_occupancy
  stg_space__register --> int_current_space
  stg_truth__asset --> dim_asset
  stg_truth__asset --> int_asset_age
  stg_truth__building --> dim_building
  stg_truth__building --> int_current_space
  stg_truth__department --> dim_department
  stg_truth__inspection_type --> dim_inspection_type
  stg_truth__inspection_type --> fct_inspection
  stg_truth__meter --> dim_meter
  stg_truth__meter --> fct_meter_hh
  stg_truth__sensor --> fct_sensor_15min
  stg_truth__sensor --> fct_space_observed_occupancy
  stg_truth__space --> int_current_space
  stg_truth__weather --> fct_energy_daily
  stg_tt__event --> fct_timetable_event
```

## Exposure (what the dashboards read)

| Exposure | Type | Owner | Reads |
|---|---|---|---|
| p06_space_dashboard | dashboard | estates-analytics | `mart_space_utilisation`, `dim_space`, `dim_building`, `fct_space_observed_occupancy` |
| p07_maintenance_dashboard | dashboard | estates-analytics | `mart_asset_health`, `fct_work_order`, `dim_asset`, `dim_trade` |
| p08_carbon_dashboard | dashboard | estates-analytics | `mart_carbon_monthly`, `fct_energy_daily`, `dim_emission_factor` |
| p09_compliance_dashboard | dashboard | estates-analytics | `mart_compliance_status`, `fct_inspection` |
| p10_institutional_return | ml | estates-analytics | `dim_space`, `dim_building`, `fct_energy_daily` |

## Edges

| Upstream | Downstream |
|---|---|
| dim_asset | p07_maintenance_dashboard |
| dim_building | p06_space_dashboard |
| dim_building | p10_institutional_return |
| dim_date | mart_space_utilisation |
| dim_emission_factor | mart_carbon_monthly |
| dim_emission_factor | p08_carbon_dashboard |
| dim_space | mart_space_utilisation |
| dim_space | p06_space_dashboard |
| dim_space | p10_institutional_return |
| dim_trade | p07_maintenance_dashboard |
| fct_energy_daily | mart_carbon_monthly |
| fct_energy_daily | p08_carbon_dashboard |
| fct_energy_daily | p10_institutional_return |
| fct_inspection | mart_compliance_status |
| fct_inspection | p09_compliance_dashboard |
| fct_meter_hh | fct_energy_daily |
| fct_space_observed_occupancy | p06_space_dashboard |
| fct_timetable_event | mart_space_utilisation |
| fct_work_order | mart_asset_health |
| fct_work_order | p07_maintenance_dashboard |
| int_asset_age | mart_asset_health |
| int_current_space | dim_space |
| int_current_space | fct_space_observed_occupancy |
| int_current_space | fct_timetable_event |
| int_meter_hh_cleaned | fct_meter_hh |
| int_work_order_enriched | dim_trade |
| int_work_order_enriched | fct_work_order |
| mart_asset_health | p07_maintenance_dashboard |
| mart_carbon_monthly | p08_carbon_dashboard |
| mart_compliance_status | p09_compliance_dashboard |
| mart_space_utilisation | p06_space_dashboard |
| seed_academic_calendar | dim_date |
| seed_dq_snapshot | mart_dq_scorecard |
| seed_emission_factors | dim_emission_factor |
| stg_cafm__work_order | int_work_order_enriched |
| stg_insp__inspection | fct_inspection |
| stg_meter__hh_a | int_meter_hh_cleaned |
| stg_meter__hh_b | int_meter_hh_cleaned |
| stg_sensor__reading | fct_sensor_15min |
| stg_sensor__reading | fct_space_observed_occupancy |
| stg_space__register | int_current_space |
| stg_truth__asset | dim_asset |
| stg_truth__asset | int_asset_age |
| stg_truth__building | dim_building |
| stg_truth__building | int_current_space |
| stg_truth__department | dim_department |
| stg_truth__inspection_type | dim_inspection_type |
| stg_truth__inspection_type | fct_inspection |
| stg_truth__meter | dim_meter |
| stg_truth__meter | fct_meter_hh |
| stg_truth__sensor | fct_sensor_15min |
| stg_truth__sensor | fct_space_observed_occupancy |
| stg_truth__space | int_current_space |
| stg_truth__weather | fct_energy_daily |
| stg_tt__event | fct_timetable_event |

All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any real university, building or estate, and nothing here is a compliance statement.
