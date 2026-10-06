# P11 wireframe — page specs

## Page 1: Model data health

Purpose: answer "is this IFC model complete enough to trust?"

```
+------------------------------------------------------------------+
| KPI cards: Space Count | Element Count | Zero Area Spaces |       |
| Elements Without Type | Elements Without Classification          |
+------------------------------------------------------------------+
| Bar: elements by ifc_class        | Donut: area_source split     |
+------------------------------------------------------------------+
| Table: qa metrics (metric, value) from qa_report.csv import      |
+------------------------------------------------------------------+
Slicers: area_source, ifc_class. Tooltip: element name + global_id.
```

## Page 2: Space & asset explorer

Purpose: answer "which spaces/systems have missing data, and does the model
agree with the register?"

```
+------------------------------------------------------------------+
| Slicers: storey (ifc_storeys.name), classification_name          |
+------------------------------------------------------------------+
| Tree: ifc_systems.name -> element names                          |
+------------------------------------------------------------------+
| Table: recon_model_vs_register                                   |
|   room_code | building_id | nia_m2 | area_m2 | area_delta_pct   |
|   | status                                                       |
+------------------------------------------------------------------+
Sort: area_delta_pct desc. Conditional format: red where |delta|>10%.
Drill-through: room_code -> element list via element name heuristic.
```
