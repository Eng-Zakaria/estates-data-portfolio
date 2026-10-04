# Catalogue (generated from contracts)

> Synthetic source-system extracts. Truth is synthetic.

## bms_trends

BMS trends wide (one column per point, ISO with offset, N/A strings, units in header)

Business key: `timestamp`

| column | type | nullable | description |
|---|---|---|---|
| timestamp | string | False | ISO timestamp with offset |

Date candidates: `%Y-%m-%dT%H:%M:%S%z`, `%Y-%m-%dT%H:%M:%S`, `%Y-%m-%d %H:%M:%S%z`

## cafm_workorders

CAFM work orders extract (renamed headers, mixed date formats, £ costs)

Business key: `WO_Number`

| column | type | nullable | description |
|---|---|---|---|
| WO_Number | string | False | Work order id |
| AssetRef | string | False | Asset reference |
| space_id | string | True | Space id |
| building_id | string | True | Building id |
| wo_type | string | True | Order type |
| priority | string | True | Priority |
| Raised | string | False | Raised datetime |
| target_ts | string | True | Target datetime |
| started_ts | string | True | Started datetime |
| Completed | string | True | Completed datetime |
| Status | string | True | Status (Complete/COMP/Closed/Open/OPEN/Outstanding) |
| trade | string | True | Trade |
| contractor | string | True | Contractor |
| labour_hours | string | True | Labour hours as string |
| Cost | string | True | Cost e.g. £1 |
| fault_code | string | True | Fault code |
| description | string | True | Description |

Date candidates: `%d/%m/%Y %H:%M`, `%Y-%m-%dT%H:%M:%S`, `%d-%b-%y %H:%M`, `%Y-%m-%d %H:%M:%S%z`, `%d/%m/%Y`, `%Y-%m-%d`

## meter_hh_supplierA

Supplier A long-format HH, local time dd/mm/yyyy HH:MM, gaps deliberate

Business key: `meter_id, local_time`

| column | type | nullable | description |
|---|---|---|---|
| meter_id | string | False | Meter id |
| local_time | string | False | Local datetime dd/mm/yyyy HH:MM |
| kwh | string | False | kWh as string (may be negative/spiked) |
| unit | string | True | Unit |

Date candidates: `%d/%m/%Y %H:%M`, `%d/%m/%Y %H:%M:%S`, `%Y-%m-%d %H:%M`

## meter_hh_supplierB

Supplier B wide-format HH (one row per meter-day, HH01.. columns), local dates

Business key: `meter_id, local_date`

| column | type | nullable | description |
|---|---|---|---|
| meter_id | string | False | Meter id |
| local_date | string | False | Local date |

Date candidates: `%Y-%m-%d`, `%d/%m/%Y`

## sensors

Sensor readings tidy parquet (drift/stuck/dropout faults present)

Business key: `sensor_id, ts_utc`

| column | type | nullable | description |
|---|---|---|---|
| sensor_id | string | False | Sensor id |
| ts_utc | string | False | UTC timestamp |
| value | string | False | Reading value as string |

Date candidates: `%Y-%m-%dT%H:%M:%S%z`, `%Y-%m-%d %H:%M:%S%z`, `%Y-%m-%dT%H:%M:%S`, `%Y-%m-%d`

## space_register

Space register extract (per-campus sheets, merged titles, names not IDs)

Business key: `Room`

| column | type | nullable | description |
|---|---|---|---|
| building_name | string | False | Building name (not ID) |
| Room | string | False | Room code |
| category_messy | string | False | Space category as recorded |
| area_text | string | True | Area text e.g. '45.2 m2'/'sqm' |
| Seats | string | True | Capacity seats as string |

## statutory_inspections

Statutory inspections (free-text results, Excel serials and text dates)

Business key: `inspection_id`

| column | type | nullable | description |
|---|---|---|---|
| inspection_id | string | False | Inspection id |
| building_id | string | False | Building id |
| inspection_type_id | string | False | Inspection type |
| due_messy | string | False | Due date (text or Excel serial) |
| completed_messy | string | True | Completed date (text or Excel serial) |
| result_text | string | True | Free-text result |
| certificate_ref | string | True | Certificate ref |

Date candidates: `%Y-%m-%d`, `%d/%m/%Y`, `%Y-%m-%dT%H:%M:%S`, `excel_serial`

## timetable

Timetable module-style export (times as HH:MM-HH:MM, weeks as ranges)

Business key: `event_id`

| column | type | nullable | description |
|---|---|---|---|
| event_id | string | False | Event id |
| space_id | string | False | Space id |
| date | string | False | Local date |
| time | string | False | Time range HH:MM-HH:MM |
| weeks | string | True | Weeks range e.g. 1-10 |
| module_code | string | True | Module code |
| group_size | string | True | Group size as string |

Date candidates: `%Y-%m-%d`, `%d/%m/%Y`
