<!-- GENERATED FILE. Do not edit by hand: run `make p20-build` (src/generate.py). CI fails if this page is stale. -->

# Business glossary (generated)

The words estates people use, with owner, source and current quality.

61 terms. Definitions are hand-written in `glossary.yml`; the DQ score column is joined from the P03 run when one exists in this checkout.

| Term | Definition | Owner | Source of truth | Refresh | DQ score | Classification |
|---|---|---|---|---|---|---|
| AIR (Asset Information Requirements) | The employer's list of what must be delivered with a project so the building can be operated: data, documents, training and spares. | estates-bim | project brief (template in the P20 handover guide) | per_release | concept, not dataset-scored | internal |
| Area mismatch | A matched room where model area and register area differ by more than ten per cent. | estates-bim | P11 reconcile output (synthetic) | per_release | concept, not dataset-scored | internal |
| Area source completeness | Share of model area that can be attributed to a space in the register. | estates-bim | IFC space and element tables (synthetic) | per_release | concept, not dataset-scored | internal |
| Asset risk band | High, medium or low priority band from criticality and condition grade. | estates-operations | dim_asset (synthetic) | monthly | 99.7/100 (assets, run output) | internal |
| Available hours | Teaching hours a space could have been booked for in the period. | estates-planning | academic calendar (dim_date) x mart_space_utilisation | per_release | 93.0/100 (timetable, run output) | internal |
| Backlog age | How long an open job has been open, banded as 0-30, 31-90, 91-180, 180+ days. | estates-operations | fct_work_order (synthetic) | daily | 95.3/100 (work_orders, run output) | internal |
| Baseload | The demand that never drops below a floor, usually overnight plant and servers. | estates-energy | derived from fct_meter_hh (no gold column yet) | monthly | 100.0/100 (bms, run output) | internal |
| Booked hours | Hours a space was booked by timetable events in the period. | estates-planning | fct_timetable_event via mart_space_utilisation | monthly | 93.0/100 (timetable, run output) | internal |
| CDE (Common Data Environment) | The shared, controlled place where project information is approved and issued. | estates-bim | UK BIM Framework Part C states (encoded in P14) | annual | concept, not dataset-scored | public |
| COBie | A standard set of spreadsheets for handing over building information, one table per topic such as components, spaces and systems. | estates-bim | buildingSMART / UK BIM Framework structure, encoded in P12 rules | annual | concept, not dataset-scored | public |
| Compliance risk score | A 0-4 score used to order the compliance action list. | estates-hs | mart_compliance_status (synthetic) | daily | 99.4/100 (inspections, run output) | internal |
| Cost per square metre | Work-order cost divided by gross internal area. | estates-operations | fct_work_order, dim_building (synthetic) | monthly | 95.3/100 (work_orders, run output) | internal |
| Data quality score | Weighted pass rate across the quality checks defined for a dataset. | estates-analytics | P03 dq_scores output (synthetic run r7) | daily | concept, not dataset-scored | internal |
| Days overdue | Days between the due date and completion, or between due date and as-of date if open. | estates-hs | mart_compliance_status (synthetic) | daily | 99.4/100 (inspections, run output) | internal |
| Degree day | A count of how far the outside temperature was below a reference, used to explain heating demand. | estates-energy | weather-derived (synthetic fct_energy_daily.hdd) | daily | 100.0/100 (bms, run output) | internal |
| Due within 30 days | Inspections falling due in the next 30 days from the as-of date. | estates-hs | mart_compliance_status (synthetic) | daily | 99.4/100 (inspections, run output) | internal |
| Emissions intensity | Emissions per square metre of gross internal area. | estates-energy | mart_carbon_monthly, dim_building (synthetic) | monthly | 82.9/100 (meters_b, run output) | public |
| Energy intensity | Energy used per square metre of gross internal area. | estates-energy | fct_energy_daily, dim_building (synthetic) | monthly | 85.8/100 (meters_a, run output) | public |
| Frequency percentage | Share of available hours in which the space was booked at least once. | estates-planning | mart_space_utilisation (synthetic) | monthly | 93.0/100 (timetable, run output) | internal |
| FTE (Full-Time Equivalent) | A headcount expressed as a fraction of a full post, so 0.5 FTE is half a full-time person. Used as the denominator for space-per-person metrics. | estates-planning | department register (synthetic dim_department.staff_fte, student_fte) | annual | concept, not dataset-scored | internal |
| GHG Protocol | The international standard used to classify emissions into scopes. | estates-energy | GHG Protocol Corporate Standard (referenced, not reproduced) | annual | concept, not dataset-scored | public |
| GIA (Gross Internal Area) | Floor area measured to the inside face of external walls, including corridors, stairs and plant rooms. It is the denominator used for energy and carbon intensity. | estates-planning | space register (synthetic dim_building.gia_m2) | on_change | 99.9/100 (spaces, run output) | internal |
| Half-hourly data | Meter readings taken every 30 minutes, the standard settlement format for electricity and gas. | estates-energy | meter supplier files (synthetic fct_meter_hh) | daily | 85.8/100 (meters_a, run output) | internal |
| HESA EMR | A UK sector-specific data return that institutions submit about their estate. | estates-finance | HESA guidance (not fetched: awareness only) | annual | concept, not dataset-scored | public |
| IFC classification | A code attached to an element that says what it is, so other systems can group it. | estates-bim | IFC property sets (synthetic sample model) | per_release | concept, not dataset-scored | internal |
| IFC element | A single building object exported from an IFC model, for example a wall or a valve. | estates-bim | IFC export tables (synthetic, written by the P11 extractor) | per_release | concept, not dataset-scored | internal |
| IFC GlobalId | The 22-character identifier an IFC model gives each object, stable across file versions. | estates-bim | P18 entity crosswalk (synthetic IFC export) | per_release | concept, not dataset-scored | internal |
| ISO 19650 | An international standard for managing information over the life of a built asset, covering containers, naming, statuses and who is allowed to do what. | estates-bim | UK National Annex encoded in P14 conventions (structure and code lists) | annual | concept, not dataset-scored | public |
| kgCO2e | Kilograms of carbon dioxide equivalent: the effect of a gas expressed as the equivalent mass of CO2, so methane counts more than CO2. | estates-energy | mart_carbon_monthly with DESNZ 2025 factors (synthetic energy) | monthly | 82.9/100 (meters_b, run output) | public |
| kWh (kilowatt hour) | A unit of energy: the amount used by one kilowatt for one hour. | estates-energy | half-hourly meter files (synthetic fct_meter_hh, fct_energy_daily) | daily | 85.8/100 (meters_a, run output) | internal |
| MTBF (Mean Time Between Failures) | Average gap in days between consecutive failures of the same asset. | estates-operations | fct_work_order, dim_asset (synthetic) | monthly | 95.3/100 (work_orders, run output) | internal |
| MTTR (Mean Time To Repair) | Average days from raising a reactive job to completing it. | estates-operations | fct_work_order (synthetic) | daily | 95.3/100 (work_orders, run output) | internal |
| NIA (Net Internal Area) | Floor area inside the external walls but excluding circulation, stairs, plant and wall thickness. It is the number estates use for space per person. | estates-planning | space register (synthetic dim_space.nia_m2) | on_change | 99.9/100 (spaces, run output) | internal |
| No-show | A timetable event where sensors saw nobody in the space during the event window. | estates-planning | fct_timetable_event joined to fct_space_observed_occupancy (synthetic) | daily | 93.2/100 (sensors, run output) | internal |
| Occupancy rate | Average fill of a booked space, as average group size over seat capacity. | estates-planning | mart_space_utilisation (synthetic) | monthly | 93.0/100 (timetable, run output) | internal |
| Open work order | A work order not yet completed at the reporting date. | estates-operations | fct_work_order (synthetic) | daily | 95.3/100 (work_orders, run output) | internal |
| Overdue | Past its due date with no recorded completion, measured against the as-of date. | estates-hs | mart_compliance_status (synthetic) | daily | 99.4/100 (inspections, run output) | internal |
| PPM (Planned Preventive Maintenance) | Maintenance carried out to a planned schedule rather than in response to a failure. | estates-operations | CAFM work orders (synthetic fct_work_order) | daily | 95.3/100 (work_orders, run output) | internal |
| Quarantined row | A row that failed a check and was held back from the analysis layer. | estates-analytics | P03 dq_failed_rows output | daily | concept, not dataset-scored | internal |
| RAG status | Red, amber or green label summarising a compliance position. | estates-hs | mart_compliance_status (synthetic) | daily | 99.4/100 (inspections, run output) | internal |
| Reactive work | Work raised because something has broken or failed a check. | estates-operations | CAFM work orders (synthetic fct_work_order) | daily | 95.3/100 (work_orders, run output) | internal |
| Releasable area | Area that would be in excess if every space were used at least to a chosen target utilisation. A planning what-if, not a saving. | estates-planning | mart_space_utilisation (synthetic) | monthly | 93.0/100 (timetable, run output) | internal |
| Remaining life | Share of an asset's expected design life still to run. | estates-operations | mart_asset_health (synthetic) | monthly | 99.7/100 (assets, run output) | internal |
| Remedial action | The work agreed after a failed inspection, tracked to closure. | estates-hs | inspection register remedial records (synthetic) | daily | 99.4/100 (inspections, run output) | internal |
| Remedial ageing | Days an open remedial action has been open. | estates-hs | inspection register remedial records (synthetic) | daily | 99.4/100 (inspections, run output) | internal |
| Renewal forecast | Replacement cost expected in each future year. | estates-operations | dim_asset (synthetic) | annual | 99.7/100 (assets, run output) | internal |
| Renewal year | The year an asset is expected to need replacing. | estates-operations | dim_asset (synthetic) | monthly | 99.7/100 (assets, run output) | internal |
| Repeat failure | An asset with three or more reactive jobs in twelve months. | estates-operations | mart_asset_health (synthetic) | monthly | 95.3/100 (work_orders, run output) | internal |
| Rolling 12-month total | A total over the twelve months to the end of each month. | estates-energy | mart_carbon_monthly (synthetic) | monthly | 82.9/100 (meters_b, run output) | public |
| Room match | The pairing of a register room with a room in an IFC model. | estates-bim | P11 reconcile output (synthetic) | per_release | concept, not dataset-scored | internal |
| Scope 1 emissions | Emissions from fuel burned inside the estate boundary, here gas combustion. | estates-energy | mart_carbon_monthly (GHG Protocol, awareness-level reference) | monthly | 82.9/100 (meters_b, run output) | public |
| Scope 2 emissions | Indirect emissions from purchased electricity, location-based. | estates-energy | mart_carbon_monthly (GHG Protocol, awareness-level reference) | monthly | 85.8/100 (meters_a, run output) | public |
| SFG20 | A UK benchmarking scheme that sets standard energy and carbon values for building services. | estates-energy | SFG20 publications (not fetched: awareness only) | annual | concept, not dataset-scored | public |
| SLA target | The agreed number of days to finish a job, by priority. | estates-operations | configuration in methodology.md (illustrative, not a contract) | on_change | 95.3/100 (work_orders, run output) | internal |
| Space per FTE | Net internal area divided by FTE, for a department or the estate. | estates-planning | derived from dim_space and dim_department | monthly | 99.9/100 (spaces, run output) | internal |
| Statutory inspection | A recorded check with a due date and an outcome (pass, fail or advisory). | estates-hs | inspection register (synthetic fct_inspection) | daily | 99.4/100 (inspections, run output) | internal |
| TRAC | The UK research funding council's sustainability reporting guidance. | estates-energy | UKRI guidance (not fetched: awareness only) | annual | concept, not dataset-scored | public |
| Uniclass | A classification of construction products and spaces that lets systems group like with like. | estates-bim | NBS Uniclass tables (not fetched: dev placeholder in P13) | annual | concept, not dataset-scored | public |
| UTC storage, UK display | All timestamps are stored in UTC and shown in UK local time in reports. | estates-analytics | platform convention (naming and modelling standards) | static | concept, not dataset-scored | internal |
| Utilisation | How much a space is used, combining booking frequency with fill when booked. | estates-planning | mart_space_utilisation (synthetic) | monthly | 93.0/100 (timetable, run output) | internal |
| Variance to pathway | How far actual emissions sit above or below a straight line to the net zero year. | estates-energy | mart_carbon_monthly (synthetic) | quarterly | 82.9/100 (meters_b, run output) | public |

## Notes and misreadings

- **AIR (Asset Information Requirements)**: An estates organisation normally holds one AIR template plus per-project addenda; the template here is a portfolio-level draft.
- **Area mismatch**: The 10% threshold is a triage convention.
- **Area source completeness**: Measures space assignment, not geometry quality.
- **Asset risk band**: A convention, not a calibrated risk model.
- **Available hours**: Teaching days times a 9-hour day; evenings and holidays are not counted.
- **Backlog age**: Missing raise date gives an "unknown" band, never zero.
- **Baseload**: Reported as a percentage of daily peak; the overnight window is a convention stated in the P08 measures.
- **Booked hours**: Double bookings count twice.
- **CDE (Common Data Environment)**: State transitions WIP, Shared, Published, Archive are implemented in P14 checks.
- **COBie**: Referenced for structure only; no COBie text is reproduced here.
- **Compliance risk score**: A triage ordering, not a legal risk assessment.
- **Cost per square metre**: Labour and materials only, on GIA not NIA.
- **Data quality score**: Measures the checks as much as the data: more checks can lower the score.
- **Days overdue**: Negative means completed early.
- **Degree day**: Useful for comparing a cold month with a mild one; not a weather correction.
- **Due within 30 days**: A workload signal, not a capacity forecast.
- **Emissions intensity**: Buildings with missing GIA are excluded from the ratio but counted in totals.
- **Energy intensity**: Not weather-normalised; degree days are available if you need them.
- **Frequency percentage**: A single booking in a rarely opened room scores almost zero.
- **FTE (Full-Time Equivalent)**: A student FTE is not a headcount: a part-time or international student counts for less than one.
- **GHG Protocol**: Used for scope definitions only in P08 methodology.
- **GIA (Gross Internal Area)**: Never compare GIA with NIA in the same sentence: NIA is always the smaller number. P19 warns that OSM footprints are not floor area at all.
- **Half-hourly data**: Two suppliers use different formats; P01 normalises them.
- **HESA EMR**: P10 is a mock return, not an official HESA submission.
- **IFC classification**: The Uniclass mapper (P13) is a development placeholder in this repository, so no official code list is applied.
- **IFC element**: An element the extractor cannot read is invisible to every BIM metric here.
- **IFC GlobalId**: A GlobalId match proves an identifier was carried, not that the geometry or classification is right.
- **ISO 19650**: Referenced for workflow and identifier conventions, not reproduced.
- **kgCO2e**: Factors are refetched each year and change retroactively in principle.
- **kWh (kilowatt hour)**: Electricity and gas kWh are not interchangeable when comparing demand.
- **MTBF (Mean Time Between Failures)**: Needs at least two failures per asset; other assets are excluded.
- **MTTR (Mean Time To Repair)**: Open jobs are excluded, so a growing backlog does not show up in MTTR.
- **NIA (Net Internal Area)**: Summed to a building or an estate; do not add NIA across duplicate space records.
- **No-show**: Only defined for events with sensor coverage. Uncovered events are blank, not counted as no-shows.
- **Occupancy rate**: Timetable-based. Sensor-observed headcounts live in a separate fact (fct_space_observed_occupancy) and will not match.
- **Open work order**: Includes jobs waiting on parts or access.
- **Overdue**: Always read the as-of date on the dashboard before quoting this.
- **PPM (Planned Preventive Maintenance)**: A closed PPM job counts as complete whether or not evidence was attached.
- **Quarantined row**: A quarantined row is not a deleted row; it is kept with a reason.
- **RAG status**: Green can mean "nothing recorded", which is the most misread cell on the compliance dashboard.
- **Reactive work**: The opposite of planned work. A reactive job that was forecast still counts as reactive in this data.
- **Releasable area**: Ignores decant cost, shared space and teaching quality.
- **Remaining life**: Negative when an asset is past its expected life.
- **Remedial action**: Closed in the tracker means closed in the tracker, not verified on site.
- **Remedial ageing**: Open actions only, so closing old items improves the average.
- **Renewal forecast**: A floor, not a total: undated assets are dropped.
- **Renewal year**: Install year plus expected life; unknown when either field is missing.
- **Repeat failure**: Counts jobs, not root causes.
- **Rolling 12-month total**: The first eleven months are partial and should be excluded.
- **Room match**: Fuzzy matching can be confidently wrong; matches are reviewed, not verified.
- **Scope 1 emissions**: Only fuels in the register are counted.
- **Scope 2 emissions**: Market-based figures would need contractual instruments this pipeline does not hold.
- **SFG20**: No SFG20 values are stored in this repository.
- **SLA target**: Targets here are P1 1 day, P2 5, P3 10, P4 20. Illustrative only.
- **Space per FTE**: Excludes space not tagged to a department, so the estate figure is lower than a floor-by-floor sum.
- **Statutory inspection**: Frequencies in the register are illustrative and are not a statement of legal duty.
- **TRAC**: No TRAC categories are encoded here.
- **Uniclass**: Status in this repository is mock, not implemented. See the standards register.
- **UTC storage, UK display**: Mixing local and UTC timestamps is the most common cause of a wrong daily total.
- **Utilisation**: Defined here as frequency x occupancy. Other teams define it differently, so always quote the definition with the number.
- **Variance to pathway**: The straight line is a planning convention, not an official pathway.

## Dashboard KPI coverage

| Dashboard KPI | Glossary term |
|---|---|
| Area Source Completeness | Area source completeness |
| Available Hours | Available hours |
| Avg Occupancy % | Occupancy rate |
| Baseload Pct | Baseload |
| Compliance Trend Overdue | Overdue |
| Days Overdue | Days overdue |
| Due Within 30 Days | Due within 30 days |
| Elements Without Classification | IFC classification |
| Elements Without Type | IFC element |
| Emissions Intensity kgCO2e per m2 | Emissions intensity |
| Energy Intensity kWh per m2 | Energy intensity |
| Failed Remedial Open | Remedial action |
| Frequency % | Frequency percentage |
| NIA m2 | NIA (Net Internal Area) |
| No-show % | No-show |
| Overdue Count | Overdue |
| RAG Status | RAG status |
| Releasable m2 (what-if) | Releasable area |
| Remedial Ageing Days | Remedial ageing |
| Risk Score | Compliance risk score |
| Rolling 12M kgCO2e | Rolling 12-month total |
| Rooms Matched | Room match |
| Rooms Missing From Model | Room match |
| Rooms Over 10pct Area Mismatch | Area mismatch |
| Scope 1 kgCO2e | Scope 1 emissions |
| Scope 2 kgCO2e | Scope 2 emissions |
| Timetabled Hours | Booked hours |
| Total Emissions kgCO2e | kgCO2e |
| Total Energy kWh | kWh (kilowatt hour) |
| Total Inspections | Statutory inspection |
| Utilisation % | Utilisation |
| Utilisation vs Target | Utilisation |
| Variance to Median | Space per FTE |
| Variance to Pathway Pct | Variance to pathway |
| age_band | Backlog age |
| cost_per_m2 | Cost per square metre |
| is_repeat_failure | Repeat failure |
| m2 per Staff FTE | FTE (Full-Time Equivalent) |
| m2 per Student FTE | FTE (Full-Time Equivalent) |
| mtbf | MTBF (Mean Time Between Failures) |
| mttr | MTTR (Mean Time To Repair) |
| planned_reactive_ratio | Reactive work |
| ppm_completion | PPM (Planned Preventive Maintenance) |
| remaining_life_pct | Remaining life |
| renewal_forecast | Renewal forecast |
| renewal_year | Renewal year |
| risk_band | Asset risk band |
| sla_met | SLA target |

All data in this pack is synthetic. Numbers come from the portfolio's generator, not from any real university, building or estate, and nothing here is a compliance statement.
