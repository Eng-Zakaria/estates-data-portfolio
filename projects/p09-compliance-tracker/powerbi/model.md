# P09 Power BI model (synthetic)

Source: `data/gold/*.parquet` via `queries/*.pq` (`GoldFolder` parameter).

## Tables and columns used

| Table | Grain | Key columns used |
|---|---|---|
| dim_building | building | building_id, building_name, campus |
| dim_inspection_type | type | inspection_type_id, inspection_name, frequency_months |
| fct_inspection | inspection | inspection_id, building_id, inspection_type_id, due_date, completed_date, result |
| remedial_actions (P09-generated) | remedial | remedial_id, inspection_id, building_id, inspection_type_id, opened_date, closed_date, description, contractor, estimated_cost_gbp |
| dim_asset | asset | asset_id, building_id, criticality (for risk score join via inspection_type.applies_to) |
| dim_date | day | date_day (for calendar/snapshots) |

Hidden: internal surrogate keys, UTC internals.
Date table: `dim_date[date_day]`. No RLS (portfolio demo).

## Relationships (single direction)

- fct_inspection[building_id] → dim_building[building_id]
- fct_inspection[inspection_type_id] → dim_inspection_type[inspection_type_id]
- remedial_actions[inspection_id] → fct_inspection[inspection_id]
- fct_inspection[inspection_type_id] → dim_inspection_type[inspection_type_id]