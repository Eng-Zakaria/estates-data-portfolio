# P18 SPEC (copy of docs/specs section - traceability)

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
