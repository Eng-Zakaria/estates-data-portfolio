# Digital twin, spatial and governance projects P18-P20

These support "Net Zero programme, Campus Digital Twin and Smart Campus projects", plus data governance, documentation and data-literacy training.

Depends on: foundation, P04 gold, P11 (IFC GUIDs), P15/P17 (sensors) where available. Build P18 with whatever exists; it must degrade gracefully if a source is missing.

---

## P18: Digital twin data layer

**Location:** `projects/p18-digital-twin-layer/`
**Criteria:** E4, E6, D5, D6, D7
**Stack:** DuckDB, Python, rdflib + brickschema, FastAPI, Pydantic, Streamlit or a small HTML + Cytoscape.js explorer, pytest.
**Positioning (put in README):** this is the **data foundation** of a digital twin (identity, relationships, time series, context), not a 3D visualisation. Explain why that is the hard and valuable part.

### Core model
1. **Canonical IDs** (`bldg:B007`, `space:B007-L02-014`, `asset:A-B007-000123`, `point:...`, `meter:...`, `ifc:<GlobalId>`).
2. **`entity_crosswalk`:** one row per (canonical_id, system, native_id) covering space register, CAFM, IFC GlobalId, BMS point, meter and sensor identifiers.
3. **`relationship`** (subject_id, predicate, object_id, source, valid_from, valid_to) with predicates aligned to Brick where practical: `hasPart`, `isLocatedIn`, `feeds`, `hasPoint`, `isMeteredBy`, `isServedBy`.
4. **Time-series access layer** over `fct_meter_hh`, `fct_sensor_15min` and BMS aggregates.

### Brick Schema model
Generate Brick TTL for at least one building: an AHU system feeding terminal units and spaces, with points (temperature, damper, CO₂), validated using `brickschema` (SHACL/ontology validation where available; verify API). Provide ≥ 5 SPARQL queries, for example "rooms served by AHU X with CO₂ above threshold yesterday" and "condition-D assets in rooms over 100 m²", each with expected results in tests.

### API (FastAPI, with OpenAPI docs)
`/buildings`, `/buildings/{id}/spaces`, `/spaces/{id}` (assets, sensors, meters, latest readings, open work orders, inspections), `/assets/{id}/timeseries?from&to&agg=15min|hour|day`, `/graph/neighbors/{id}?depth=2`, `/coverage`. Pagination, API-key header (demo key via `.env`), consistent error model, tests with `TestClient`, Dockerfile.

### Explorer UI
Building → space → asset tree; relationship graph; clicking an AHU shows served spaces and a sensor trend. Keep it small and robust.

### Integrity and coverage
Orphan detection, ID-collision tests, crosswalk completeness. `twin_coverage` report: % assets with IFC GlobalId, % spaces with sensors, % assets linked to a BMS point, % meters mapped to a building.

### Optional stretch (do not block)
Embed a web IFC viewer (for example That Open Engine / web-ifc) to highlight a space selected in the explorer.

### Acceptance
- Graph traversal tests (for example from AHU to all spaces served) match the generator's truth.
- All API endpoints covered by tests; OpenAPI schema committed.
- Brick model validates; SPARQL examples return the expected sets.
- Coverage report included in README with measured numbers.

**CV bullet:** *Designed a campus digital-twin data layer: canonical IDs and a cross-system crosswalk linking space, asset, IFC, BMS and meter data, a Brick Schema model, and a REST API serving context plus time series.*

---

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

## P20: Governance and data-literacy pack

**Location:** `projects/p20-governance-literacy/` (MkDocs Material site published to GitHub Pages)
**Criteria:** E7, plus responsibilities: "Promote good practice in data governance, documentation, and repeatable workflows" and "Support training and engagement activities to improve data literacy"
**Stack:** MkDocs Material, mkdocs-mermaid plugin, Python scripts that generate pages from dbt `manifest.json`/`catalog.json`, data contracts and DQ results, textstat (readability), pytest, a link checker.

### Content (each item a short, usable page, not boilerplate)
1. **Governance framework:** principles; roles (owner, steward, custodian, consumer); RACI per domain (space, assets, energy/carbon, compliance, BIM); decision rights; escalation path.
2. **Data dictionary and business glossary:** auto-generated columns and tables from dbt/contracts; hand-written glossary for GIA, NIA, FTE, PPM, reactive, MTTR, utilisation, Scope 1/2, baseload, COBie, AIR, etc. Each entry: definition, owner, source of truth, refresh frequency, current DQ score.
3. **Metric registry** (`metrics.yml`): id, name, definition, formula, grain, owner, source model, caveats, version. **Test:** every KPI named in P06-P10 dashboards and `measures.dax` files exists in the registry, and vice versa.
4. **Data classification and handling:** public / internal / confidential; where personal data could appear in estates data (for example names on work orders) and how it is handled; UK GDPR awareness note (state it is not legal advice).
5. **Data quality policy:** link to P03 (dimensions, thresholds, severity, response times).
6. **Naming and modelling standards:** tables, columns, IDs, units, time zones (UTC storage, UK display).
7. **Standards register:** ISO 19650, Uniclass, COBie, SFG20, HESA EMR/TRAC, GHG Protocol: what each is, where it touches the data, owner, and **honest status** (implemented / mock / awareness-only).
8. **Information handover guide:** project → operations checklist linking P12/P14, AIR template, roles.
9. **Data request and change process:** intake form template, triage criteria, SLA, metric-change log.
10. **"How to read our dashboards" guide:** one page per dashboard (P06-P10, DQ scorecard): the question it answers, how to read each visual, common misreadings, definitions, refresh time, limitations, who to ask. Plain English.
11. **Training kit:** 10-minute demo script; 45-minute "Data literacy for Estates" workshop (learning outcomes, three exercises using the synthetic dashboards, answer key, 10-question quiz, feedback form); slide outline only (the human builds the slides); facilitator notes.
12. **Runbooks and ADR index** linking to the other projects' docs.

### Automation
Scripts regenerate dictionary, lineage and DQ-score pages from artifacts; CI fails if generated pages are stale, links are broken, or the metric-registry test fails.

### Acceptance
- `mkdocs build --strict` passes; link checker clean.
- Glossary and metric registry cover 100% of dashboard KPIs (test).
- Literacy guide readability measured (target Flesch reading ease ≥ 50); numbers reported, not hidden.
- Workshop pack is complete enough that someone else could deliver it from the folder alone.
