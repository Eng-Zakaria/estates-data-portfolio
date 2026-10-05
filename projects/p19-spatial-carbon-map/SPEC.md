# P19 SPEC (copy of docs/specs section - traceability)

## P19: Spatial analysis and carbon map

**Location:** `projects/p19-spatial-carbon-map/`
**Criteria:** E3, E5, D5, D8
**Stack:** GeoPandas, shapely, pyproj, osmnx (OpenStreetMap), folium, `topojson` or mapshaper for export, matplotlib, pytest.

### Data and honesty
- Building footprints from OpenStreetMap for a configurable bounding box (the area of any university campus; default to an arbitrary open campus area). **Use geometry only; anonymise names** ("Building A"...) and assign campus_synth building IDs to footprints by a documented rule (for example area-rank match). Attribution: OpenStreetMap contributors, ODbL; record in `DATA.md`.
- All metrics (energy, carbon, work orders) are synthetic. Every map carries a "synthetic metrics on public geometry" footnote.

### Analyses
1. Footprint area vs GIA sanity check (implied storeys; flag outliers).
2. **kgCO₂e/m² choropleth** and energy hotspots (from P08 tables).
3. Heat-demand clustering: distance matrix between buildings and candidate plant locations; cluster buildings within a configurable distance and sum their gas demand per cluster, as a *screening-level* "district heating candidate" view. State clearly it is not a feasibility study.
4. Walking isochrones (5/10 min) from a chosen building using the OSM walking network; space and demand within each isochrone.
5. CRS handling: do area/distance calculations in a projected CRS (EPSG:27700 for UK or the local equivalent) and export web layers in EPSG:4326; test that areas match a known polygon.

### Outputs
GeoPackage; GeoJSON and TopoJSON; static PNG maps; interactive Folium HTML; a QGIS style file (`.qml`) as a stretch; Power BI handoff for a map page (Shape Map using the TopoJSON, or point/bubble map from lat/long; check which visuals are available) following the AGENTS.md protocol.

### Acceptance
- Geometry validity tests (no invalid or empty geometries), CRS tests, distance-matrix tests against known points.
- Reproducible: `make p19` fetches (or uses a cached OSM extract in `data/`) and builds all outputs.
- README documents CRS decisions, limits (footprint ≠ floor area; OSM completeness) and attribution.

---
