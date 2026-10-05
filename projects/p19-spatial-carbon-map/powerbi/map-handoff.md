# P19 Power BI map-page handoff (synthetic metrics on public geometry)

## Option A — Shape Map with custom TopoJSON (preferred)
1. Get data: `outputs/campus_carbon.topojson` is the custom map. In Power BI:
   Shape Map visual → "Add map" → Custom map → import the TopoJSON.
2. Data table: import `outputs/campus_carbon.geojson` attributes (or the
   `building_geo` CSV below) with `building_id` as the join key. The TopoJSON
   features carry `building_id`; Shape Map matches colour values to map keys.
3. Colour field: `kgco2e_per_m2` (5 quantile breaks in `build.log.json`).
   Set Shape Map → Shape → Color scale (YlGn equivalent).

## Option B — Bubble/point map fallback (no custom visual needed)
Import `outputs/building_points.csv` (`building_id, anon_name, lat, lon,
kgco2e_per_m2, gas_kwh`); use the Azure Map / Map visual with bubble size =
`gas_kwh`, colour saturation = `kgco2e_per_m2`.

## Wireframe — map page
```
+----------------------------------------------------------+
| Shape Map: campus choropleth kgCO2e/m2 (B007 darkest)    |
| Slicers: heat cluster, storey-flag only                  |
+----------------------------------------------------------+
| Cards: matched buildings (8) | clusters (4) | biggest    |
|  cluster gas kWh (117,375, cluster 2)                    |
+----------------------------------------------------------+
| Footer: "Synthetic metrics on public geometry (c)       |
|  OpenStreetMap contributors"                             |
+----------------------------------------------------------+
```

## Validation
Counts: 8 matched buildings; intensity ranking ties to P08 `v02`
(B007 top). Re-run `make p19` after any P04 rebuild and re-check.
