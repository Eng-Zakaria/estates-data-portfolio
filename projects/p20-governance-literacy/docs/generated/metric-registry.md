<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). CI fails if this page is stale. -->

# Metric registry (generated)

Every published number: what it means, how it is built, what it cannot tell you.

74 entries: 69 published on a dashboard, 5 planned. This page is generated from `metrics.yml`, which is the source of truth.

| Metric | Id | Kind | Status | Grain | Owner | Version | Dashboards |
|---|---|---|---|---|---|---|---|
| Area Source Completeness | area_source_completeness | metric | live | IFC model, building | estates-bim | 1.0.0 | p11 |
| Asset IFC Coverage % | asset_ifc_coverage_pct | metric | planned | building, asset type | estates-bim | 0.1.0 | p18 |
| Available Hours | available_hours | metric | live | estate x academic year | estates-planning | 1.0.0 | p06 |
| Avg Occupancy % | avg_occupancy_pct | metric | live | space, building, category | estates-planning | 1.0.0 | p06 |
| Backlog Count | p07_backlog_count | metric | live | building, trade, priority, age band | estates-operations | 1.0.0 | p07 |
| Baseload Pct | baseload_pct | metric | live | meter, building, month | estates-energy | 1.0.0 | p08 |
| Compliance Trend Overdue | compliance_trend_overdue | helper | live | month, building, inspection type | estates-hs | 1.0.0 | p09 |
| Cost per m2 £ | p07_cost_per_m2_gbp | metric | live | building, trade, month | estates-operations | 1.0.0 | p07 |
| DQ Failed Rows | dq_failed_rows | metric | planned | dataset, reason, day | estates-analytics | 0.1.0 | p03 |
| DQ Score | dq_score | metric | planned | dataset, dataset x dimension, building | estates-analytics | 0.1.0 | p03 |
| Days Overdue | compliance_days_overdue | metric | live | inspection | estates-hs | 1.0.0 | p09 |
| Due Within 30 Days | due_within_30_days | metric | live | building, inspection type, month | estates-hs | 1.0.0 | p09 |
| Element Count | p11_element_count | metric | live | IFC model, building | estates-bim | 1.0.0 | p11 |
| Elements Without Classification | elements_without_classification | metric | live | IFC model, building | estates-bim | 1.0.0 | p11 |
| Elements Without Type | elements_without_type | metric | live | IFC model, building | estates-bim | 1.0.0 | p11 |
| Emissions Intensity kgCO2e per m2 | emissions_intensity_kgco2e_m2 | metric | live | month, building, estate | estates-energy | 1.0.0 | p08 |
| Energy Intensity kWh per m2 | energy_intensity_kwh_m2 | metric | live | month, building, estate | estates-energy | 1.0.0 | p08 |
| Failed Remedial Open | failed_remedial_open | metric | live | building, inspection type, month | estates-hs | 1.0.0 | p09 |
| Failing Error Checks | failing_error_checks | metric | planned | run, dataset | estates-analytics | 0.1.0 | p03 |
| Frequency % | frequency_pct | metric | live | space, building, category | estates-planning | 1.0.0 | p06 |
| MTTR Days | p07_mttr_days | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| NIA m2 | nia_m2 | metric | live | space, building | estates-planning | 1.0.0 | p06 |
| No-show % | no_show_pct | metric | live | space, building, date | estates-planning | 1.0.0 | p06 |
| Open Work Orders | open_work_orders | metric | planned | building, trade, priority, age band | estates-operations | 0.1.0 | p07 |
| Overdue Count | overdue_count | metric | live | building, inspection type, month | estates-hs | 1.0.0 | p09 |
| PPM Completion % | p07_ppm_completion_dax | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| Planned : Reactive | p07_planned_reactive | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| Pool Total | p10_pool_total | metric | live | return pack, pool x activity | estates-finance | 1.0.0 | p10 |
| RAG Status | rag_status | helper | live | building, inspection type | estates-hs | 1.0.0 | p09 |
| Reactive 12m | p07_reactive_12m | metric | live | asset, building, asset type | estates-operations | 1.0.0 | p07 |
| Releasable m2 (what-if) | releasable_m2 | metric | live | space, building, estate | estates-planning | 1.0.0 | p06 |
| Remaining Life % | p07_remaining_life | metric | live | building, asset type | estates-operations | 1.0.0 | p07 |
| Remedial Ageing Days | remedial_ageing_days | metric | live | remedial action, inspection | estates-hs | 1.0.0 | p09 |
| Renewal Forecast £ | p07_renewal_forecast_gbp | metric | live | year, asset type, building | estates-operations | 1.0.0 | p07 |
| Repeat Failure Assets | p07_repeat_failure_assets_dax | metric | live | building, asset type | estates-operations | 1.0.0 | p07 |
| Risk Score | compliance_risk_score | metric | live | building, inspection type | estates-hs | 1.0.0 | p09 |
| Rolling 12M kgCO2e | rolling_12m_kgco2e | metric | live | month, fuel, estate | estates-energy | 1.0.0 | p08 |
| Rooms Matched | rooms_matched | helper | live | building, room | estates-bim | 1.0.0 | p11 |
| Rooms Missing From Model | rooms_missing_from_model | metric | live | building, room | estates-bim | 1.0.0 | p11 |
| Rooms Over 10pct Area Mismatch | rooms_over_10pct_area_mismatch | metric | live | building, room | estates-bim | 1.0.0 | p11 |
| SLA Met % | p07_sla_met | metric | live | priority, trade, building, month | estates-operations | 1.0.0 | p07 |
| Scope 1 kgCO2e | scope_1_kgco2e | metric | live | month, fuel, building | estates-energy | 1.0.0 | p08 |
| Scope 2 kgCO2e | scope_2_kgco2e | metric | live | month, fuel, building | estates-energy | 1.0.0 | p08 |
| Space Count | p11_space_count | metric | live | IFC model, building | estates-bim | 1.0.0 | p11 |
| Timetabled Hours | timetabled_hours | metric | live | space (aggregable to building, estate) | estates-planning | 1.0.0 | p06 |
| Total CO2e | p10_total_co2e | metric | live | return pack, month, building x fuel | estates-energy | 1.0.0 | p10 |
| Total Cost £ | p07_total_cost | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| Total Emissions kgCO2e | total_emissions_kgco2e | metric | live | month, fuel, building | estates-energy | 1.0.0 | p08 |
| Total Energy kWh | total_energy_kwh | metric | live | date, building, fuel, meter | estates-energy | 1.0.0 | p08, p10 |
| Total GIA | p10_total_gia | metric | live | return pack, building | estates-finance | 1.0.0 | p10 |
| Total Inspections | total_inspections | metric | live | building, inspection type, month | estates-hs | 1.0.0 | p09 |
| Total NIA | p10_total_nia | metric | live | return pack, building x return category | estates-finance | 1.0.0 | p10 |
| Total WOs | p07_total_wos | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| Utilisation % | utilisation_pct | metric | live | space, building, category | estates-planning | 1.0.0 | p06 |
| Utilisation vs Target | utilisation_vs_target | metric | live | space, building, estate | estates-planning | 1.0.0 | p06 |
| Validation Blocking | p10_validation_blocking | metric | live | return pack, rule | estates-finance | 1.0.0 | p10 |
| Validation Query | p10_validation_query | metric | live | return pack, rule | estates-finance | 1.0.0 | p10 |
| Variance to Median | variance_to_median | metric | live | department | estates-planning | 1.0.0 | p06 |
| Variance to Pathway Pct | variance_to_pathway_pct | metric | live | year, fuel, estate | estates-energy | 1.0.0 | p08 |
| Zero Area Spaces | p11_zero_area_spaces | metric | live | IFC model, building | estates-bim | 1.0.0 | p11 |
| age_band | backlog_age_band | helper | live | work order | estates-operations | 1.0.0 | p07 |
| cost_per_m2 | cost_per_m2 | metric | live | building, trade, month | estates-operations | 1.0.0 | p07 |
| is_repeat_failure | repeat_failure_assets | metric | live | asset | estates-operations | 1.0.0 | p07 |
| m2 per Staff FTE | m2_per_staff_fte | metric | live | department, faculty, estate | estates-planning | 1.0.0 | p06 |
| m2 per Student FTE | m2_per_student_fte | metric | live | department, faculty, estate | estates-planning | 1.0.0 | p06 |
| mtbf | mtbf | metric | live | asset, asset type, building | estates-operations | 1.0.0 | p07 |
| mttr | mttr | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| planned_reactive_ratio | planned_reactive_ratio | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| ppm_completion | ppm_completion | metric | live | estate, building, trade, month | estates-operations | 1.0.0 | p07 |
| remaining_life_pct | remaining_life_pct | metric | live | asset, asset type | estates-operations | 1.0.0 | p07 |
| renewal_forecast | renewal_forecast_gbp | metric | live | year, asset type, building | estates-operations | 1.0.0 | p07 |
| renewal_year | renewal_year | helper | live | asset | estates-operations | 1.0.0 | p07 |
| risk_band | asset_risk_band | helper | live | asset | estates-operations | 1.0.0 | p07 |
| sla_met | sla_met_pct | metric | live | priority, trade, building, month | estates-operations | 1.0.0 | p07 |

## Area Source Completeness

- **Definition**: Share of model area that can be attributed to a source space, i.e. whether the model can be costed or analysed by room.
- **Formula**: `sum(area of elements with a space) / sum(area of all elements)`
- **Grain**: IFC model, building
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_element.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: Area source completeness - Share of model area that can be attributed to a space in the register.
- **Caveats**:
    - Area means gross element volume-derived area as exported by the extractor, not NIA.
    - Completeness of space assignment, not of geometry.

## Asset IFC Coverage %

- **Definition**: Share of register assets that can be linked to an IFC GlobalId in the twin crosswalk.
- **Formula**: `100 * count(assets with an ifc GlobalId) / count(assets)`
- **Grain**: building, asset type
- **Owner**: `estates-bim`
- **Source model**: `file:projects/p18-digital-twin-layer/outputs/entity_crosswalk.csv`, `dim_asset`
- **Version**: 0.1.0
- **Status**: planned (kind: metric)
- **Classification**: internal
- **Dashboards**: `p18`
- **Glossary**: IFC GlobalId - The 22-character identifier an IFC model gives each object, stable across file versions.
- **Caveats**:
    - {'Planned': 'P18 computes this in its coverage report; it is not on a dashboard.'}
    - A GlobalId match proves an identifier was carried, not that the geometry is correct.

## risk_band

- **Definition**: Priority band for an asset from criticality and condition grade.
- **Formula**: `criticality * condition weight (A=1,B=2,C=3,D=4); >=16 High, >=9 Medium, else Low`
- **Grain**: asset
- **Owner**: `estates-operations`
- **Source model**: `dim_asset`
- **Version**: 1.0.0
- **Status**: live (kind: helper)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Asset risk band - High, medium or low priority band from criticality and condition grade.
- **Caveats**:
    - Helper banding, not a risk model; weights are a convention and are not calibrated against failure data.
    - Unknown condition or criticality returns None (shown as Unknown), never Low.

## Available Hours

- **Definition**: Teaching hours a room could have been booked for in the reporting window: teaching days (not weekend, not holiday) multiplied by a 9-hour teaching day.
- **Formula**: `count(dates where teaching_week > 0 and not weekend and not holiday) * 9`
- **Grain**: estate x academic year
- **Owner**: `estates-planning`
- **Source model**: `dim_date`, `mart_space_utilisation`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Available hours - Teaching hours a space could have been booked for in the period.
- **Caveats**:
    - Assumes a 9-hour day and does not model room-by-room opening hours.
    - Counts teaching weeks only, so term-time booking patterns are visible but evening use is not.

## Avg Occupancy %

- **Definition**: Average fill of a booked room, as average group size over seat capacity.
- **Formula**: `avg(mart_space_utilisation.occupancy_rate)`
- **Grain**: space, building, category
- **Owner**: `estates-planning`
- **Source model**: `mart_space_utilisation`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Occupancy rate - Average fill of a booked space, as average group size over seat capacity.
- **Caveats**:
    - Synthetic group size comes from the timetable, not from sensors; P17 observed counts are a separate fact.
    - {'Unweighted mean of room-level rates': 'many tiny rooms count as much as one lecture theatre.'}

## age_band

- **Definition**: Bands an open job by how long it has been open: 0-30, 31-90, 91-180, 180+ days, or unknown.
- **Formula**: `fixed thresholds on age in days`
- **Grain**: work order
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: helper)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Backlog age - How long an open job has been open, banded as 0-30, 31-90, 91-180, 180+ days.
- **Caveats**:
    - Helper banding, not a KPI; thresholds are conventions, not standards.
    - Unknown age (missing raise date) returns None and is shown as a separate bar, never as zero.

## Baseload Pct

- **Definition**: Share of peak demand that continues overnight, as an indicator of always-on load.
- **Formula**: `avg(overnight minimum kW) / avg(daily peak kW) * 100`
- **Grain**: meter, building, month
- **Owner**: `estates-energy`
- **Source model**: `fct_meter_hh`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p08`
- **Glossary**: Baseload - The demand that never drops below a floor, usually overnight plant and servers.
- **Caveats**:
    - Needs an hourly calculation table or a Power BI computed column; there is no gold column for it yet.
    - Overnight window and minimum are conventions (P08 measures.dax states both); change them and the number changes.
    - High baseload can be legitimate plant load, not only waste.

## Days Overdue

- **Definition**: Days between the due date and completion, or between due date and as-of date if still open.
- **Formula**: `date_diff(day, due_date, coalesce(completed_date, as_of_date))`
- **Grain**: inspection
- **Owner**: `estates-hs`
- **Source model**: `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Days overdue - Days between the due date and completion, or between due date and as-of date if open.
- **Caveats**:
    - Negative for completed-early inspections; read those as headroom, not a credit.
    - Calendar days, no working-time or notice-period adjustment.

## Risk Score

- **Definition**: 0-4 score ranking compliance risk from status and overdue days, used to order the action list.
- **Formula**: `banded from status (0 compliant to 4 failed with open remedial) and days overdue`
- **Grain**: building, inspection type
- **Owner**: `estates-hs`
- **Source model**: `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Compliance risk score - A 0-4 score used to order the compliance action list.
- **Caveats**:
    - A triage ordering, not a legal risk assessment; bands are conventions in the mart.
    - Scores are not comparable across inspection types.

## Compliance Trend Overdue

- **Definition**: Month-by-month count of overdue inspections used for the trend line.
- **Formula**: `count(overdue) grouped by month`
- **Grain**: month, building, inspection type
- **Owner**: `estates-hs`
- **Source model**: `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: helper)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Overdue - Past its due date with no recorded completion, measured against the as-of date.
- **Caveats**:
    - Helper for the trend visual; it inherits every caveat of overdue count.
    - Month boundaries follow the synthetic calendar, not inspection seasons.

## cost_per_m2

- **Definition**: Work-order cost per square metre of gross internal area.
- **Formula**: `cost_gbp / gia_m2`
- **Grain**: building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`, `dim_building`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Cost per square metre - Work-order cost divided by gross internal area.
- **Caveats**:
    - Uses GIA (the building envelope) deliberately, unlike P06 which uses NIA.
    - Labour and materials only; excludes overheads and capital spend.

## DQ Failed Rows

- **Definition**: Rows that failed at least one check and were quarantined, by dataset and reason.
- **Formula**: `count(distinct quarantined rows) grouped by dataset and reason`
- **Grain**: dataset, reason, day
- **Owner**: `estates-analytics`
- **Source model**: `dq:data/quality/gold/dq_failed_rows.parquet`
- **Version**: 0.1.0
- **Status**: planned (kind: metric)
- **Classification**: internal
- **Dashboards**: `p03`
- **Glossary**: Quarantined row - A row that failed a check and was held back from the analysis layer.
- **Caveats**:
    - {'Planned': 'available as a P03 output, not yet published in a mart.'}
    - A row can fail several checks and is attributed to the first quarantine reason in pipeline order.

## DQ Score

- **Definition**: Weighted pass rate across data quality checks for one dataset.
- **Formula**: `100 * sum(weight * pass_rate) / sum(weight)`
- **Grain**: dataset, dataset x dimension, building
- **Owner**: `estates-analytics`
- **Source model**: `dq:data/quality/gold/dq_scores.parquet`
- **Version**: 0.1.0
- **Status**: planned (kind: metric)
- **Classification**: internal
- **Dashboards**: `p03`
- **Glossary**: Data quality score - Weighted pass rate across the quality checks defined for a dataset.
- **Caveats**:
    - {'Planned': 'scores exist in P03 output but are not yet a dbt mart or a dashboard measure.'}
    - Score is relative to the checks defined, so it measures the framework as much as the data.

## Due Within 30 Days

- **Definition**: Inspections falling due in the next 30 days from the as-of date.
- **Formula**: `count(mart_compliance_status where status = 'Due within 30 days')`
- **Grain**: building, inspection type, month
- **Owner**: `estates-hs`
- **Source model**: `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Due within 30 days - Inspections falling due in the next 30 days from the as-of date.
- **Caveats**:
    - A forward-looking workload signal from the mart's own status logic, not a forecast of contractor capacity.

## Elements Without Classification

- **Definition**: IFC elements carrying no classification code that a downstream mapper can use.
- **Formula**: `count(elements where classification is null or empty)`
- **Grain**: IFC model, building
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_element.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: IFC classification - A code attached to an element that says what it is, so other systems can group it.
- **Caveats**:
    - P13's Uniclass mapping is a dev placeholder, so a null classification here does not mean the code list was consulted.

## Elements Without Type

- **Definition**: IFC elements with no type or classification attached, so their function is unknown to downstream systems.
- **Formula**: `count(elements where type or classification is missing)`
- **Grain**: IFC model, building
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_element.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: IFC element - A single building object exported from an IFC model, for example a wall or a valve.
- **Caveats**:
    - Counts elements the extractor could read; elements missing from the export are invisible here.
    - "Unclassified" is a modelling defect, not a data-quality bug in this pipeline.

## Emissions Intensity kgCO2e per m2

- **Definition**: Emissions per square metre of gross internal area.
- **Formula**: `sum(kgco2e) / sum(dim_building.gia_m2)`
- **Grain**: month, building, estate
- **Owner**: `estates-energy`
- **Source model**: `mart_carbon_monthly`, `dim_building`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p08`
- **Glossary**: Emissions intensity - Emissions per square metre of gross internal area.
- **Caveats**:
    - Denominator is GIA; buildings with missing GIA are excluded from the ratio but still counted in totals.
    - No normalisation for degree days or opening hours.

## Energy Intensity kWh per m2

- **Definition**: Energy used per square metre of gross internal area.
- **Formula**: `sum(kwh) / sum(dim_building.gia_m2)`
- **Grain**: month, building, estate
- **Owner**: `estates-energy`
- **Source model**: `fct_energy_daily`, `dim_building`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p08`
- **Glossary**: Energy intensity - Energy used per square metre of gross internal area.
- **Caveats**:
    - Uses GIA, so it is not comparable with P06's NIA-based ratios.
    - Weather and occupancy are not normalised here; degree days are available in fct_energy_daily.hdd if you want to.

## Failed Remedial Open

- **Definition**: Failed inspections that still have an open remedial action.
- **Formula**: `count(mart_compliance_status where status = 'Failed - remedial open')`
- **Grain**: building, inspection type, month
- **Owner**: `estates-hs`
- **Source model**: `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Remedial action - The work agreed after a failed inspection, tracked to closure.
- **Caveats**:
    - Open means not closed in the tracker; an action closed without evidence still counts as closed.
    - The red RAG band is driven by this measure alone.

## Failing Error Checks

- **Definition**: Number of checks currently failing at error severity, the CI gate signal.
- **Formula**: `count(checks where severity = 'error' and status = 'fail')`
- **Grain**: run, dataset
- **Owner**: `estates-analytics`
- **Source model**: `dq:data/quality/gold/dq_alerts.parquet`
- **Version**: 0.1.0
- **Status**: planned (kind: metric)
- **Classification**: internal
- **Dashboards**: `p03`
- **Glossary**: Quarantined row - A row that failed a check and was held back from the analysis layer.
- **Caveats**:
    - {'Planned': 'the gate runs this in CI but there is no dashboard page for it yet.'}
    - One failing check on a tiny dataset can outrank a large volume of passing checks.

## Frequency %

- **Definition**: Share of available room hours that were booked at least once.
- **Formula**: `timetabled hours / (count of spaces * available hours)`
- **Grain**: space, building, category
- **Owner**: `estates-planning`
- **Source model**: `mart_space_utilisation`, `dim_date`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Frequency percentage - Share of available hours in which the space was booked at least once.
- **Caveats**:
    - A room booked for 1 hour in 500 available hours scores 0.2%, which reads as "unused" in a room that is barely usable.
    - Understates demand for rooms with limited opening hours.

## m2 per Staff FTE

- **Definition**: Net internal area available to a department per full-time-equivalent staff member.
- **Formula**: `sum(dim_space.nia_m2) / sum(dim_department.staff_fte)`
- **Grain**: department, faculty, estate
- **Owner**: `estates-planning`
- **Source model**: `dim_space`, `dim_department`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: FTE (Full-Time Equivalent) - A headcount expressed as a fraction of a full post, so 0.5 FTE is half a full-time person. Used as the denominator for space-per-person metrics.
- **Caveats**:
    - NIA is allocated to a department only when the space is tagged to it; untagged space is excluded, which lowers the estate figure.
    - FTE counts are synthetic and static for the window.

## m2 per Student FTE

- **Definition**: Net internal area available per full-time-equivalent student.
- **Formula**: `sum(dim_space.nia_m2) / sum(dim_department.student_fte)`
- **Grain**: department, faculty, estate
- **Owner**: `estates-planning`
- **Source model**: `dim_space`, `dim_department`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: FTE (Full-Time Equivalent) - A headcount expressed as a fraction of a full post, so 0.5 FTE is half a full-time person. Used as the denominator for space-per-person metrics.
- **Caveats**:
    - {'Same allocation caveat as staff': 'untagged space is excluded.'}
    - Part-time and international students are counted as FTE, not headcount.

## mtbf

- **Definition**: Mean time between failures: average gap between consecutive failures of the same asset.
- **Formula**: `mean(diff(sorted(failure dates))) over assets with >= 2 failures`
- **Grain**: asset, asset type, building
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`, `dim_asset`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: MTBF (Mean Time Between Failures) - Average gap in days between consecutive failures of the same asset.
- **Caveats**:
    - Only defined for assets with two or more failures; singletons return None, so averages exclude them.
    - {'Synthetic failure dates': 'expect a value for every asset in this demo.'}

## mttr

- **Definition**: Mean time to repair: average days from raising to completing a reactive job.
- **Formula**: `mean(days_to_complete) over reactive jobs with a completion`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: MTTR (Mean Time To Repair) - Average days from raising a reactive job to completing it.
- **Caveats**:
    - Open jobs are excluded, so a long backlog is invisible in MTTR; pair with backlog age band.
    - Calendar days, not working hours; waits on parts or access count.

## NIA m2

- **Definition**: Net Internal Area in square metres: floor area measured inside the external walls.
- **Formula**: `sum(dim_space.nia_m2)`
- **Grain**: space, building
- **Owner**: `estates-planning`
- **Source model**: `dim_space`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: NIA (Net Internal Area) - Floor area inside the external walls but excluding circulation, stairs, plant and wall thickness. It is the number estates use for space per person.
- **Caveats**:
    - Excludes corridors, stairs, plant and external walls by definition; never compare with GIA.
    - Synthetic values; the register is the source of truth, not OSM footprints (P19).

## No-show %

- **Definition**: Share of covered timetable events where sensors saw nobody in the room during the event window.
- **Formula**: `events with no_show_flag = 1 / events with a non-blank no_show_flag`
- **Grain**: space, building, date
- **Owner**: `estates-planning`
- **Source model**: `fct_timetable_event`, `fct_space_observed_occupancy`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: No-show - A timetable event where sensors saw nobody in the space during the event window.
- **Caveats**:
    - Needs the calculated column built in Power Query from validation/v02_rooms_to_review.sql; without sensor coverage the denominator shrinks and the number can move for the wrong reason.
    - {'A no-show is not proof of absence': 'sensors can fail (see P17 sensor health).'}

## Open Work Orders

- **Definition**: Work orders not yet completed at the reporting date.
- **Formula**: `count(fct_work_order where is_open)`
- **Grain**: building, trade, priority, age band
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 0.1.0
- **Status**: planned (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Open work order - A work order not yet completed at the reporting date.
- **Caveats**:
    - {'Planned': 'P07 validation SQL v02 computes it, but there is no measures.dax entry yet.'}
    - Open includes jobs awaiting parts or access, not only jobs not started.

## Overdue Count

- **Definition**: Inspections whose due date has passed without a recorded completion.
- **Formula**: `count(mart_compliance_status where status = 'Overdue')`
- **Grain**: building, inspection type, month
- **Owner**: `estates-hs`
- **Source model**: `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Overdue - Past its due date with no recorded completion, measured against the as-of date.
- **Caveats**:
    - Overdue against a synthetic as-of date; use the as-of slicer, not today's date.
    - Excludes failed inspections with remedial actions, which have their own measure.

## Backlog Count

- **Definition**: Work orders not yet completed at the reporting date.
- **Formula**: `countrows(fct_work_order where is_open)`
- **Grain**: building, trade, priority, age band
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Open work order - A work order not yet completed at the reporting date.
- **Caveats**:
    - Open includes jobs awaiting parts or access, not only jobs not started.
    - {'A count, not a cost': 'a backlog of small jobs can look worse than one large one.'}

## Cost per m2 £

- **Definition**: Work-order cost per square metre of gross internal area.
- **Formula**: `sum(fct_work_order.cost_gbp) / sum(dim_building.gia_m2)`
- **Grain**: building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`, `dim_building`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Cost per square metre - Work-order cost divided by gross internal area.
- **Caveats**:
    - Same definition as the Python helper cost_per_m2.
    - Uses GIA (the building envelope) deliberately, unlike P06 which uses NIA.
    - Labour and materials only; excludes overheads and capital spend.

## MTTR Days

- **Definition**: Mean time to repair: average days from raising to completing a reactive job.
- **Formula**: `average(fct_work_order.days_to_complete where wo_type = 'Reactive' and status = 'Complete')`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: MTTR (Mean Time To Repair) - Average days from raising a reactive job to completing it.
- **Caveats**:
    - Same definition as the Python helper mttr.
    - Open jobs are excluded, so a long backlog is invisible in MTTR; pair with backlog age band.
    - Calendar days, not working hours; waits on parts or access count.

## Planned : Reactive

- **Definition**: Planned work per reactive job: how much of the workload was scheduled rather than called out.
- **Formula**: `countrows(fct_work_order where plan_category in ('planned','other_planned')) / countrows(fct_work_order where wo_type = 'Reactive')`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Reactive work - Work raised because something has broken or failed a check.
- **Caveats**:
    - Same definition as the Python helper planned_reactive_ratio.
    - None when there are no reactive jobs in scope.
    - A high ratio can also mean under-reporting of breakdowns, so read with MTTR and repeat failures.

## PPM Completion %

- **Definition**: Planned preventive maintenance jobs completed in the period, over planned jobs due in the period.
- **Formula**: `countrows(fct_work_order where wo_type = 'PPM' and status = 'Complete') / countrows(fct_work_order where wo_type = 'PPM')`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: PPM (Planned Preventive Maintenance) - Maintenance carried out to a planned schedule rather than in response to a failure.
- **Caveats**:
    - Same definition as the Python helper ppm_completion; the two artefacts are kept in step by the coverage test.
    - {'Counts closure, not quality': 'a job closed with no evidence still counts.'}

## Reactive 12m

- **Definition**: Reactive jobs per asset in the last twelve months, at asset grain.
- **Formula**: `sum(mart_asset_health.reactive_12m)`
- **Grain**: asset, building, asset type
- **Owner**: `estates-operations`
- **Source model**: `mart_asset_health`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Reactive jobs in 12 months - The number of breakdown jobs raised against one asset in the last twelve months.
- **Caveats**:
    - A sum of per-asset counts, so it is a workload total, not a distinct-job count.
    - Assets with no reactive jobs contribute zero, which is the point.

## Remaining Life %

- **Definition**: Average share of expected design life still to run across assets.
- **Formula**: `average(mart_asset_health.remaining_life_pct)`
- **Grain**: building, asset type
- **Owner**: `estates-operations`
- **Source model**: `mart_asset_health`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Remaining life - Share of an asset's expected design life still to run.
- **Caveats**:
    - Same definition as the Python helper remaining_life_pct, averaged.
    - Negative for assets past design life; report as-is.
    - Design life is a single number per type and ignores condition survey evidence.

## Renewal Forecast £

- **Definition**: Replacement cost expected in each future year from assets reaching end of life.
- **Formula**: `sum(dim_asset.replacement_cost_gbp) grouped by renewal_year`
- **Grain**: year, asset type, building
- **Owner**: `estates-operations`
- **Source model**: `dim_asset`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Renewal forecast - Replacement cost expected in each future year.
- **Caveats**:
    - Same definition as the Python helper renewal_forecast.
    - Undated assets are dropped, so the forecast is a floor, not a total.
    - Replacement cost is a register figure, not a quotation; no inflation applied.

## Repeat Failure Assets

- **Definition**: Count of assets flagged as repeat failures: three or more reactive jobs in twelve months.
- **Formula**: `countrows(mart_asset_health where is_repeat_failure)`
- **Grain**: building, asset type
- **Owner**: `estates-operations`
- **Source model**: `mart_asset_health`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Repeat failure - An asset with three or more reactive jobs in twelve months.
- **Caveats**:
    - Same definition as the Python helper is_repeat_failure, applied as a count.
    - Threshold of three is a portfolio convention, not a standard; change it and the count changes.
    - {'Counts jobs, not root causes': 'one fault fixed four times looks like four different failures.'}

## SLA Met %

- **Definition**: Share of completed jobs finished inside the priority's response target.
- **Formula**: `count(completed jobs where days_to_complete <= target) / count(completed jobs with a target)`
- **Grain**: priority, trade, building, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: SLA target - The agreed number of days to finish a job, by priority.
- **Caveats**:
    - Same definition as the Python helper sla_met.
    - Targets are illustrative (P1 1d, P2 5d, P3 10d, P4 20d), set in methodology.md, not by contract.
    - {'Open jobs are excluded': 'the percentage can look healthy while the backlog grows.'}

## Total Cost £

- **Definition**: Total work-order cost in pounds over the selected period.
- **Formula**: `sum(fct_work_order.cost_gbp)`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Work-order cost - The labour and materials cost recorded against a work order, in pounds.
- **Caveats**:
    - Labour and materials only; excludes overheads and capital spend.
    - Includes open jobs, so a period with a large unfinished job looks expensive.

## Total WOs

- **Definition**: Total work orders raised in the selected period, whatever their type or status.
- **Formula**: `countrows(fct_work_order)`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Work order - A single job raised in the maintenance system, with a type, priority, dates and cost.
- **Caveats**:
    - {'Counts jobs, not value': 'one small job counts the same as a large one.'}
    - Includes open jobs, so it is a workload measure, not a completed-work measure.

## Pool Total

- **Definition**: Total cost allocated across activity pools in the return pack.
- **Formula**: `sum(cost_allocation[allocated_gbp])`
- **Grain**: return pack, pool x activity
- **Owner**: `estates-finance`
- **Source model**: `file:data/p10_output/cost_allocation_<date>.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p10`
- **Glossary**: Cost allocation - Sharing a pool of cost across activities using a chosen driver, such as floor area or staff numbers.
- **Caveats**:
    - {'Allocated cost, not measured cost': 'it is a share of a pool chosen by a driver such as floor area or staff numbers.'}
    - Driver totals sit beside the allocation so the split can be checked by hand.

## Total CO2e

- **Definition**: Emissions in the return pack, summed from the pack's emissions table.
- **Formula**: `sum(emissions[kgco2e])`
- **Grain**: return pack, month, building x fuel
- **Owner**: `estates-energy`
- **Source model**: `file:data/p10_output/emissions_<date>.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p10`
- **Glossary**: kgCO2e - Kilograms of carbon dioxide equivalent: the effect of a gas expressed as the equivalent mass of CO2, so methane counts more than CO2.
- **Caveats**:
    - Same location-based basis as the carbon mart, so it must agree with it; a difference means a filter or a refresh mismatch.
    - {'Labelled CO2e in the return pack and kgCO2e in the mart': 'the same quantity, two labels.'}

## Total GIA

- **Definition**: Gross internal area summed once per building: each building's area is counted a single time, then added across buildings.
- **Formula**: `sumx(VALUES(building_areas[building_id]), CALCULATE(MAX(building_areas[gia_m2])))`
- **Grain**: return pack, building
- **Owner**: `estates-finance`
- **Source model**: `file:data/p10_output/building_areas_<date>.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p10`
- **Glossary**: GIA (Gross Internal Area) - Floor area measured to the inside face of external walls, including corridors, stairs and plant rooms. It is the denominator used for energy and carbon intensity.
- **Caveats**:
    - {'Deliberately de-duplicated per building': 'a building with several return categories has one area, not one per category.'}
    - Takes the maximum area per building, so a building with two area rows uses the larger one. Say so rather than fixing it silently.

## Total NIA

- **Definition**: Net internal area summed over the buildings and return categories in the return pack.
- **Formula**: `sum(building_areas[nia_m2])`
- **Grain**: return pack, building x return category
- **Owner**: `estates-finance`
- **Source model**: `file:data/p10_output/building_areas_<date>.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p10`
- **Glossary**: NIA (Net Internal Area) - Floor area inside the external walls but excluding circulation, stairs, plant and wall thickness. It is the number estates use for space per person.
- **Caveats**:
    - The return pack is a mock; the categories are illustrative, not official HESA or funder codes.
    - Totals depend on the category mapping, so a mapping change moves this number without any physical change.

## Validation Blocking

- **Definition**: Number of validation breaches in the return pack that block the pack being issued.
- **Formula**: `countrows(FILTER(validation_report, validation_report[severity] = 'blocking'))`
- **Grain**: return pack, rule
- **Owner**: `estates-finance`
- **Source model**: `file:data/p10_output/validation_<date>.yaml`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p10`
- **Glossary**: Validation rule - A check run inside a pack that either blocks the pack being issued or raises a question about it.
- **Caveats**:
    - {'A count of rules that fired, not a severity ranking': 'one breach is one breach.'}
    - A clean validation file means the internal checks passed; it is not an assurance opinion.

## Validation Query

- **Definition**: Number of validation findings in the return pack that ask a question rather than block it.
- **Formula**: `countrows(FILTER(validation_report, validation_report[severity] = 'query'))`
- **Grain**: return pack, rule
- **Owner**: `estates-finance`
- **Source model**: `file:data/p10_output/validation_<date>.yaml`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p10`
- **Glossary**: Validation rule - A check run inside a pack that either blocks the pack being issued or raises a question about it.
- **Caveats**:
    - Findings labelled "query" need a human answer before the pack is issued; they are not automatic failures.
    - Counts findings, not the size of the problem behind each one.

## Element Count

- **Definition**: Number of building elements extracted from the IFC model, such as AHUs, boilers, pumps and fan coil units.
- **Formula**: `countrows(ifc_elements)`
- **Grain**: IFC model, building
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_element.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: IFC element - A single building object exported from an IFC model, for example a wall or a valve.
- **Caveats**:
    - Counts elements the extractor could read; elements missing from the export are invisible here.
    - {'A count of model elements, not of register assets': 'the two are compared by the reconciliation.'}

## Space Count

- **Definition**: Number of spaces extracted from the IFC model.
- **Formula**: `countrows(ifc_spaces)`
- **Grain**: IFC model, building
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_space.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: Space - A room or area in the space register, with a building, a category and a net internal area.
- **Caveats**:
    - Counts spaces the extractor could read; spaces missing from the export are invisible here.
    - {'A count of model spaces, not of register rooms': 'the two are compared by the room-match measures.'}

## Zero Area Spaces

- **Definition**: Spaces in the IFC model with no area or a non-positive area, found by QA.
- **Formula**: `countrows(ifc_spaces where area_m2 <= 0)`
- **Grain**: IFC model, building
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_space.csv`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: Zero-area space - A space in an IFC model with no area or a non-positive area, found by QA.
- **Caveats**:
    - A modelling defect, not a data-quality bug in this pipeline.
    - In the demo model the planted defect count is one; a different count means the model changed.

## planned_reactive_ratio

- **Definition**: Planned work (planned, statutory, project) per reactive job: how much of the workload was scheduled rather than called out.
- **Formula**: `(planned + statutory + project jobs) / reactive jobs`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Reactive work - Work raised because something has broken or failed a check.
- **Caveats**:
    - None when there are no reactive jobs in scope.
    - A high ratio can also mean under-reporting of breakdowns, so read with MTTR and repeat failures.

## ppm_completion

- **Definition**: Planned preventive maintenance jobs completed in the period, over planned jobs due in the period.
- **Formula**: `completed PPM jobs / PPM jobs raised`
- **Grain**: estate, building, trade, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: PPM (Planned Preventive Maintenance) - Maintenance carried out to a planned schedule rather than in response to a failure.
- **Caveats**:
    - None when no jobs were raised; the dashboard shows blank, not zero.
    - {'Counts job closure, not work quality': 'a closed job with no evidence still counts.'}

## RAG Status

- **Definition**: Red, amber or green label for a compliance position, derived from status and remedial state.
- **Formula**: `case logic over status and open remedial actions`
- **Grain**: building, inspection type
- **Owner**: `estates-hs`
- **Source model**: `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: helper)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: RAG status - Red, amber or green label summarising a compliance position.
- **Caveats**:
    - Helper label, not a score; a green building with no records at all is still green, which is the main misreading.
    - Thresholds are conventions and are visible in the mart SQL.

## Releasable m2 (what-if)

- **Definition**: Area that would be in excess if every scope were pushed to a chosen target utilisation.
- **Formula**: `NIA m2 * (1 - utilisation % / target utilisation param)`
- **Grain**: space, building, estate
- **Owner**: `estates-planning`
- **Source model**: `mart_space_utilisation`, `dim_space`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Releasable area - Area that would be in excess if every space were used at least to a chosen target utilisation. A planning what-if, not a saving.
- **Caveats**:
    - {'What-if only': 'it does not model decant cost, shared space, statutory limits or teaching quality.'}
    - Goes negative for scopes already above target; read as "capped at zero".

## remaining_life_pct

- **Definition**: Share of an asset's expected design life still to run.
- **Formula**: `1 - age_years / expected_life_years`
- **Grain**: asset, asset type
- **Owner**: `estates-operations`
- **Source model**: `mart_asset_health`, `dim_asset`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Remaining life - Share of an asset's expected design life still to run.
- **Caveats**:
    - Negative for assets past design life; report as-is.
    - Design life is a single number per type and ignores condition survey evidence.

## Remedial Ageing Days

- **Definition**: Days since a remedial action was raised and it is still open.
- **Formula**: `date_diff(day, remedial raised date, as_of_date) where action is open`
- **Grain**: remedial action, inspection
- **Owner**: `estates-hs`
- **Source model**: `fct_inspection`, `mart_compliance_status`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Remedial ageing - Days an open remedial action has been open.
- **Caveats**:
    - Open actions only, so the average improves as old actions are closed, not as work gets done.
    - {'No severity weighting': 'a cosmetic and a safety-critical action age identically.'}

## renewal_forecast

- **Definition**: Replacement cost expected in each future year from assets reaching end of life.
- **Formula**: `sum(replacement_cost_gbp) grouped by renewal year`
- **Grain**: year, asset type, building
- **Owner**: `estates-operations`
- **Source model**: `dim_asset`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Renewal forecast - Replacement cost expected in each future year.
- **Caveats**:
    - Undated assets are dropped, so the forecast is a floor, not a total.
    - Replacement cost is a register figure, not a quotation; no inflation applied.

## renewal_year

- **Definition**: Year an asset is expected to need replacing, from install year plus expected life.
- **Formula**: `install year + expected_life_years`
- **Grain**: asset
- **Owner**: `estates-operations`
- **Source model**: `dim_asset`
- **Version**: 1.0.0
- **Status**: live (kind: helper)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Renewal year - The year an asset is expected to need replacing.
- **Caveats**:
    - {'Helper, not a KPI': 'it produces no number on its own.'}
    - Unknown install date or life returns None and is dropped from the forecast (counted as a coverage gap).

## is_repeat_failure

- **Definition**: Asset flag for three or more reactive jobs in twelve months.
- **Formula**: `reactive_12m >= 3`
- **Grain**: asset
- **Owner**: `estates-operations`
- **Source model**: `mart_asset_health`, `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: Repeat failure - An asset with three or more reactive jobs in twelve months.
- **Caveats**:
    - Threshold of three is a portfolio convention, not a standard; change it and the count changes.
    - {'Counts jobs, not root causes': 'one fault fixed four times looks like four different failures.'}

## Rolling 12M kgCO2e

- **Definition**: Emissions over the twelve months to the end of each month, to smooth seasonal swings.
- **Formula**: `sum(kgco2e) over the trailing 12 months`
- **Grain**: month, fuel, estate
- **Owner**: `estates-energy`
- **Source model**: `mart_carbon_monthly`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p08`
- **Glossary**: Rolling 12-month total - A total over the twelve months to the end of each month.
- **Caveats**:
    - The first eleven months are partial and must be excluded or annualised; the dashboard filter handles this.
    - Rolling, so one bad month stays in the series for a year.

## Rooms Matched

- **Definition**: Rooms in the space register successfully matched to a room in the IFC model.
- **Formula**: `count(register rooms with a matched model room)`
- **Grain**: building, room
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_space.csv`, `dim_space`
- **Version**: 1.0.0
- **Status**: live (kind: helper)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: Room match - The pairing of a register room with a room in an IFC model.
- **Caveats**:
    - Matched by name and number with a fuzzy fallback; near-matches can be wrong in the same way every time.
    - {'Matched is not verified': 'nobody has confirmed the pairing room by room.'}

## Rooms Missing From Model

- **Definition**: Register rooms with no counterpart in the IFC model, i.e. space the model does not describe.
- **Formula**: `count(register rooms with no matched model room)`
- **Grain**: building, room
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_space.csv`, `dim_space`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: Room match - The pairing of a register room with a room in an IFC model.
- **Caveats**:
    - A room can be missing because it was demolished, or because the model predates a refurbishment; the data cannot tell you which.

## Rooms Over 10pct Area Mismatch

- **Definition**: Matched rooms where the model's area differs from the register by more than ten per cent.
- **Formula**: `count(matched rooms where abs(model area - register area) / register area > 0.10)`
- **Grain**: building, room
- **Owner**: `estates-bim`
- **Source model**: `file:data/gold/ifc/ifc_space.csv`, `dim_space`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p11`
- **Glossary**: Area mismatch - A matched room where model area and register area differ by more than ten per cent.
- **Caveats**:
    - The 10% threshold is a convention for triage, not a tolerance agreed with the designer.
    - Model area is derived geometry; register area is a stated figure, so both can be right.

## Scope 1 kgCO2e

- **Definition**: Direct emissions from fuel burned inside the estate boundary (here, gas combustion).
- **Formula**: `sum(kgco2e where scope = 'Scope 1')`
- **Grain**: month, fuel, building
- **Owner**: `estates-energy`
- **Source model**: `mart_carbon_monthly`, `dim_emission_factor`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p08`
- **Glossary**: Scope 1 emissions - Emissions from fuel burned inside the estate boundary, here gas combustion.
- **Caveats**:
    - Covers only fuels in the register; any unmetered burner is missing rather than zero.
    - Scope definition follows GHG Protocol, awareness-level reference only.

## Scope 2 kgCO2e

- **Definition**: Indirect emissions from purchased electricity, location-based.
- **Formula**: `sum(kgco2e where scope = 'Scope 2')`
- **Grain**: month, fuel, building
- **Owner**: `estates-energy`
- **Source model**: `mart_carbon_monthly`, `dim_emission_factor`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p08`
- **Glossary**: Scope 2 emissions - Indirect emissions from purchased electricity, location-based.
- **Caveats**:
    - Location-based only. A market-based figure would need contractual instruments that this pipeline does not hold.

## sla_met

- **Definition**: Share of completed jobs finished inside the priority's response target.
- **Formula**: `count(days_to_complete <= target_days) / count(completed jobs with a target)`
- **Grain**: priority, trade, building, month
- **Owner**: `estates-operations`
- **Source model**: `fct_work_order`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p07`
- **Glossary**: SLA target - The agreed number of days to finish a job, by priority.
- **Caveats**:
    - Targets are illustrative (P1 1d, P2 5d, P3 10d, P4 20d), set in methodology.md, not by contract.
    - {'Open jobs are excluded': 'the percentage can look healthy while the backlog grows.'}

## Timetabled Hours

- **Definition**: Total booked hours of teaching events across the selected scope.
- **Formula**: `sum(mart_space_utilisation.booked_hours)`
- **Grain**: space (aggregable to building, estate)
- **Owner**: `estates-planning`
- **Source model**: `mart_space_utilisation`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Booked hours - Hours a space was booked by timetable events in the period.
- **Caveats**:
    - A double-booked room is counted twice; the timetable is not de-conflicted here.
    - Bookings with a zero group size are retained.

## Total Emissions kgCO2e

- **Definition**: Location-based greenhouse gas emissions in kilograms of CO2 equivalent.
- **Formula**: `sum(mart_carbon_monthly.kgco2e)`
- **Grain**: month, fuel, building
- **Owner**: `estates-energy`
- **Source model**: `mart_carbon_monthly`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p08`
- **Glossary**: kgCO2e - Kilograms of carbon dioxide equivalent: the effect of a gas expressed as the equivalent mass of CO2, so methane counts more than CO2.
- **Caveats**:
    - {'Location-based, not market-based': 'no renewable tariffs or certificates are claimed.'}
    - Factors are DESNZ 2025 flat-format values fetched by script; they change every year.

## Total Energy kWh

- **Definition**: Delivered energy in kilowatt hours over the selected period, across all fuels and meters.
- **Formula**: `sum(fct_energy_daily.kwh)`
- **Grain**: date, building, fuel, meter
- **Owner**: `estates-energy`
- **Source model**: `fct_energy_daily`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p08`, `p10`
- **Glossary**: kWh (kilowatt hour) - A unit of energy: the amount used by one kilowatt for one hour.
- **Caveats**:
    - Meter-read kWh, not primary energy; gas and electricity are not interchangeable units of demand.
    - Missing half-hours reduce the total; check fct_energy_daily.n_periods before comparing months.
    - {'Published by two reports': 'the carbon dashboard (mart) and the mock return pack (its own energy table). Same quantity, different filters.'}

## Total Inspections

- **Definition**: Count of inspections in scope for the period, whatever their status.
- **Formula**: `countrows(fct_inspection)`
- **Grain**: building, inspection type, month
- **Owner**: `estates-hs`
- **Source model**: `fct_inspection`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p09`
- **Glossary**: Statutory inspection - A recorded check with a due date and an outcome (pass, fail or advisory).
- **Caveats**:
    - Frequencies in the register are illustrative and are not a statement of legal duty.
    - "No record" is a status: a building can look compliant simply because nothing was logged.

## Utilisation %

- **Definition**: Room use combining how often a room is booked with how full it is when booked.
- **Formula**: `frequency % * avg occupancy %`
- **Grain**: space, building, category
- **Owner**: `estates-planning`
- **Source model**: `mart_space_utilisation`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Utilisation - How much a space is used, combining booking frequency with fill when booked.
- **Caveats**:
    - {'A product, not a time-weighted average': 'a room booked once and full for 50 people scores like a room booked daily at 50%.'}
    - Both inputs are synthetic proxies; treat as a screening view, not an estates fact.

## Utilisation vs Target

- **Definition**: Gap in percentage points between actual utilisation and the chosen target.
- **Formula**: `utilisation % - target utilisation param`
- **Grain**: space, building, estate
- **Owner**: `estates-planning`
- **Source model**: `mart_space_utilisation`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Utilisation - How much a space is used, combining booking frequency with fill when booked.
- **Caveats**:
    - {'A percentage-point difference, not a percent change': 'read "0.05" as five points, not 5%.'}

## Variance to Median

- **Definition**: How far a department's space per staff FTE sits above or below the median department.
- **Formula**: `(m2 per staff FTE - median(m2 per staff FTE)) / median(m2 per staff FTE)`
- **Grain**: department
- **Owner**: `estates-planning`
- **Source model**: `dim_space`, `dim_department`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: internal
- **Dashboards**: `p06`
- **Glossary**: Space per FTE - Net internal area divided by FTE, for a department or the estate.
- **Caveats**:
    - {'Median, not mean': 'one very large department cannot pull the benchmark.'}
    - Ignores teaching quality, lab requirements and space quality; a lab-heavy department is meant to look high.

## Variance to Pathway Pct

- **Definition**: How far actual emissions sit above or below a linear pathway to the net zero target year.
- **Formula**: `(actual - pathway) / pathway, pathway interpolated between baseline year and target year`
- **Grain**: year, fuel, estate
- **Owner**: `estates-energy`
- **Source model**: `mart_carbon_monthly`
- **Version**: 1.0.0
- **Status**: live (kind: metric)
- **Classification**: public
- **Dashboards**: `p08`
- **Glossary**: Variance to pathway - How far actual emissions sit above or below a straight line to the net zero year.
- **Caveats**:
    - {'Baseline and target year are what-if parameters (defaults': 'base year first full year, target 2040).'}
    - Linear interpolation is a planning convention, not an official pathway.

All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any real university, building or estate, and nothing here is a compliance statement.
