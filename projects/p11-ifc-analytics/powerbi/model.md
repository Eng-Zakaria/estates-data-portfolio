# P11 Power BI model (synthetic)

Source: Parquet in `data/gold/ifc/`, loaded via `queries/*.pq`. Set the
`GoldFolder` parameter to the absolute `data/gold/ifc` path before refresh.

## Tables and columns used

| Table | Grain | Key columns used |
|---|---|---|
| ifc_project | project | global_id, name |
| ifc_storeys | storey | global_id, name |
| ifc_spaces | space | global_id, name, area_m2, area_source |
| ifc_elements | element | global_id, name, ifc_class |
| ifc_types | type | global_id, name |
| ifc_systems | system | global_id, name |
| ifc_system_members | system × element | system_global_id, element_global_id |
| ifc_properties_long | element × property | global_id, pset, property, value, unit |
| ifc_quantities_long | element × quantity | global_id, qto, quantity, value, unit |
| ifc_classifications | element × classification | global_id, classification_id, classification_name |
| recon_model_vs_register | room | room_code, building_id, nia_m2, area_m2, area_delta, area_delta_pct, status |

Hidden: surrogate/internal join columns (`system_global_id`,
`element_global_id`) except in the system-member browse page.
No date table required (extract is a point-in-time snapshot); note the IFC
file hash in a text box for lineage. No RLS roles (portfolio demo).

## Relationships (many-to-one, single direction)

- ifc_spaces / ifc_elements / ifc_storeys → ifc_project (project-level grouping; via storeys where available)
- ifc_system_members[system_global_id] → ifc_systems[global_id]
- ifc_system_members[element_global_id] → ifc_elements[global_id]
- ifc_classifications[global_id] → ifc_elements[global_id]
- ifc_properties_long[global_id] → ifc_elements[global_id]
- ifc_quantities_long[global_id] → ifc_elements[global_id]

Filters flow from dimension-like tables (systems, classifications) down to
facts. Reconciliation table stands alone (room_code is not a shared key).
