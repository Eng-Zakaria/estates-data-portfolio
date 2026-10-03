# Foundation: `campus_synth` (build this first)

**Location:** `packages/campus_synth/`
**Why:** almost every project needs realistic, messy, linked estates data. One deterministic generator keeps all 20 projects consistent (same building IDs, same planted findings) and avoids any real data.
**Stack:** Python 3.12, numpy, pandas, pyarrow, openpyxl, faker (names only), Pydantic v2 config, Typer CLI, pytest.

## 1. CLI

```
campus-synth generate --profile small|default --seed 42 --out data/raw [--defects 0.0..1.0] [--format csv,xlsx,parquet]
campus-synth truth    --out data/raw/ground_truth.yaml     # planted findings registry
campus-synth snapshots --weeks 12 --out data/raw_snapshots # weekly snapshots with decreasing defect rate (for P03 trend)
```

Profiles:
- `small` (CI): 8 buildings, 3 months of data, ~500 spaces. Must generate in < 30 s.
- `default`: 40 buildings, 24 months of half-hourly data, ~3,000 spaces, ~12,000 assets, ~60,000 work orders, ~130 meters, sensors in 150 rooms for the last 3 months.

All randomness comes from a single seeded `numpy.random.Generator`. Same seed → byte-identical output (test this by hashing files).

## 2. Entities (canonical "truth" model)

IDs: `B001`..; spaces `S-B001-L02-014`; assets `A-B001-000123`; meters `M-B001-E01`; sensors `SN-...`; fake IFC GlobalIds (22-char base64-style) for ~60% of buildings' spaces/assets.

| Table | Key columns |
|---|---|
| `buildings` | building_id, building_name (anonymised "Building A".. or "Science Block 3"), campus, gia_m2, nia_m2, n_floors, year_built, primary_use, heating_fuel, epc_band, lat, lon, ifc_available |
| `floors` | floor_id, building_id, level_code, level_name |
| `departments` | department_id, name, faculty, staff_fte, student_fte |
| `spaces` | space_id, building_id, floor_id, room_code, space_category, space_type, capacity_seats, nia_m2, department_id, ifc_guid, valid_from, valid_to |
| `assets` | asset_id, building_id, space_id, asset_type, description_raw, manufacturer, model, serial_no, install_date, expected_life_years, condition_grade (A-D), criticality (1-5), replacement_cost_gbp, cobie_type, uniclass_code_true (only for ~40 mapped types, see P13), ifc_guid |
| `work_orders` | wo_id, asset_id, space_id, building_id, wo_type (PPM/Reactive/Statutory/Project), priority (P1-P4), raised_ts, target_ts, started_ts, completed_ts, status, trade, contractor, labour_hours, cost_gbp, fault_code, description |
| `inspection_types` | inspection_type_id, name, frequency_months, applies_to_asset_type (frequencies are *illustrative config*, see P09) |
| `inspections` | inspection_id, asset_id or building_id, inspection_type_id, due_date, completed_date, result (Pass/Fail/Advisory), remedial_required, certificate_ref, inspector |
| `meters` | meter_id, building_id, utility (electricity/gas/water/heat), meter_role (main/sub), parent_meter_id, unit, interval (HH/daily/register), mpan_mprn_synthetic |
| `meter_readings_hh` | meter_id, ts_utc, value, unit, quality_flag |
| `weather` | ts_utc, temp_c, hdd_base15_5, cdd |
| `academic_calendar` | date, term, teaching_week, is_holiday, is_weekend (term dates are config) |
| `timetable_events` | event_id, space_id, start_ts, end_ts, module_code, department_id, group_size, booked_capacity_need |
| `sensors` | sensor_id, space_id, sensor_type (co2/temp/rh/occupancy_count), install_date |
| `sensor_readings` | sensor_id, ts_utc, value (15-min) |
| `cost_pools` | pool_id, year, cost_type (rates, utilities, cleaning, maintenance, security), amount_gbp, allocation_driver |
| `activity_splits` | department_id, teaching_pct, research_pct, other_pct (staff-time style, synthetic) |

Generation logic that must be realistic:
- **Electricity profile** = base load + occupancy-driven daytime load (term/weekday/hour pattern) + noise; **gas** = base + heating-degree-day driven; solar gain/holiday dips; building-type differences (labs high base load, libraries long hours, residences evening peaks).
- **UK time handling:** timestamps stored in UTC; the CAFM and meter exports use *local* time, so BST/GMT changeovers create 46/50-period days. Some exports use ambiguous local times. This is deliberate.
- **Work orders** follow asset age/condition; failure rates rise with age; some assets get repeat reactive jobs; PPM schedules are regular; costs lognormal.
- **Timetable:** realistic teaching days (09:00-18:00), group sizes vs capacity with some mismatches; ~15% bookings are no-shows.
- **Sensors:** CO₂ responds to occupancy and ventilation rate (first-order model); temperature follows setpoint and occupancy; occupancy count from a noisy PIR/people-counter model.

## 3. Source-system exports (the "messy" layer)

`generate` writes **raw exports shaped like source systems**, not the clean truth tables (those go to `data/truth/` for tests and evaluation only):

| Export | Format & mess |
|---|---|
| `space_register_YYYYMMDD.xlsx` | multiple sheets per campus; merged header rows; building names not IDs; mixed category spellings; areas as text with "m2"/"sqm"; some blank rows |
| `cafm_workorders_YYYYMMDD.csv` | different header names from truth; dates in 3 formats (dd/mm/yyyy, ISO, "03-Mar-26"); status codes inconsistent; cost with £ and commas; duplicate rows |
| `meter_hh_<supplier>_YYYYMMDD.csv` | supplier A: long format; supplier B: wide format (48 columns per day); cumulative register reads for some meters; local time; missing periods |
| `bms_trends_YYYYMMDD.csv` | wide format, one column per point, ISO timestamps with offsets, "N/A" strings, units in header |
| `statutory_inspections_YYYYMMDD.xlsx` | free-text results, dates as Excel serials and text |
| `timetable_YYYYMMDD.csv` | module-style export, times as "09:00-11:00", weeks as ranges "1-10,12" |
| `sensors_YYYYMMDD.parquet` | tidy, but with drift/stuck/dropout faults |

## 4. Defect injection

`--defects` (default 0.03) controls rates. Implement `inject_defects(df, spec)` with these catalogued defect types (each logged to `ground_truth.yaml` with table, row key, type):
duplicate rows; nulls in mandatory fields; out-of-range values (negative area, cost, kWh); orphan foreign keys; misspelt categories; future dates; completed_ts before raised_ts; area totals exceeding building GIA; negative or spiked meter reads; flat-lined meters (≥ 48 identical periods); gaps; meter rollover; DST duplicates; unit mix-ups (MWh vs kWh); stale files.

## 5. Planted findings (`ground_truth.yaml`)

Seed these so dashboards and algorithms have something genuine to find. Make building IDs fixed across seeds.
- **B007:** HVAC runs overnight (baseload ≈ 60% of peak) from month 10.
- **B019:** gas heating runs through summer (control fault) for 5 weeks.
- **B012:** boiler asset with ≥ 8 reactive work orders in 12 months.
- **Teaching rooms in B003:** booked ≥ 70% of timetable hours but average occupancy < 30% of capacity.
- **Department D-ENG:** space per FTE ≈ 40% above the median.
- **Legionella-type inspections** overdue in 3 buildings; 2 failed inspections with open remedial actions older than 90 days.
- **One lecture theatre (B005):** CO₂ > 1,500 ppm in ≥ 20% of occupied time.
- **Meter M-B015-E01:** flat-lines for 5 days. **Sensor SN-0042:** drifts upward from week 6.
- **PPM completion rate** drops sharply in one quarter.
- **Asset register vs IFC:** 12 rooms in B003's IFC with area differences > 10% from the register; 5 rooms missing from the model.

`ground_truth.yaml` is consumed by tests in P03, P16, P17 and others to measure detection.

## 6. Tests and acceptance

- Determinism test (same seed → same hashes); schema tests (Pydantic) for every truth table; referential-integrity tests on the truth tables (zero orphans); defect catalogue test (injected counts equal log counts); DST test (spring-forward day has 46 periods, autumn 50 in local-time exports); planted-findings test (e.g., B007 overnight/peak ratio within the stated band).
- `small` profile < 30 s; `default` < 5 min and < 1.5 GB on disk.
- `docs/DATA_MODEL.md` with an ER diagram (Mermaid) of the truth model and a table of every export, its mess, and the truth table it maps to.
- README includes a plain-English "why synthetic" section and the full list of planted findings.

**Skills demonstrated:** E3, E4, E6 (data modelling and realistic data engineering), D5.
