# P06 Power BI model (synthetic)

Source: `data/gold/*.parquet` via `queries/*.pq` (`GoldFolder` parameter).

## Tables and columns used

| Table | Grain | Key columns used |
|---|---|---|
| dim_space | space | space_id, building_id, space_category, nia_m2, capacity_seats |
| dim_building | building | building_id, building_name, campus, gia_m2 |
| dim_department | department | department_id, department_name, staff_fte, student_fte |
| dim_date | day | date_day, teaching_week, is_holiday, is_weekend |
| fct_timetable_event | event | event_id, space_id, event_date, start_time, end_time, group_size, duration_hours |
| fct_space_observed_occupancy | sensor reading | space_id, ts_utc, observed_count |
| mart_space_utilisation | space | space_id → n_events, booked_hours, frequency_rate, occupancy_rate |
| truth spaces (dept map) | space | space_id, department_id, nia_m2 — P06-level enrichment; promote to dim_space later |

Hidden: room codes, UTC internals, `is_holiday` raw flags (use calc columns).
Date table: `dim_date[date_day]`. No RLS (portfolio demo).

## Relationships (single direction)

- fct_timetable_event[space_id] → dim_space[space_id]
- fct_timetable_event[event_date] → dim_date[date_day]
- fct_space_observed_occupancy[space_id] → dim_space[space_id]
- mart_space_utilisation[space_id] → dim_space[space_id]
- dim_space[building_id] → dim_building[building_id]
