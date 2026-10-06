# P18 Digital twin data layer

> **Synthetic data for portfolio demonstration. No real building topology or sensor data is implied.**

## 1. Problem statement

A campus digital twin needs a unified data foundation that links spaces, assets, IFC models, BMS points, meters, and sensors through canonical identities and a queryable relationship graph. This project builds that foundation: canonical IDs, a cross-system crosswalk, Brick-aligned relationships, a time-series access layer, a validated Brick Schema model, a FastAPI service, and an explorer UI — all on synthetic gold marts.

## 2. Architecture

```mermaid
flowchart LR
  GOLD[P04 gold marts<br/>spaces, assets, meters, sensors, work orders] --> IDS[src/ids.py<br/>canonical IDs + validation]
  GOLD --> CW[src/crosswalk.py<br/>entity_crosswalk: canonical↔system↔native]
  CW --> REL[src/relationships.py<br/>relationship graph with Brick predicates]
  GOLD --> TS[src/timeseries.py<br/>async TS layer over fct_meter_hh, fct_sensor_15min, BMS]
  REL --> BRICK[src/brick.py<br/>Brick TTL + SHACL validation + SPARQL]
  TS + CW + REL --> API[src/api.py<br/>FastAPI + OpenAPI + API key]
  API --> EXPL[src/explorer.py<br/>Streamlit: tree, graph, trends, coverage]
  CW + REL --> BRICK
  BRICK --> VAL[validation + SPARQL]
```

## 3. Data: sources, licences, synthetic-data note

All inputs are synthetic: P04 gold marts + truth parquet (IFC GUIDs) from `campus_synth` seed 42. No external data. Every UI/endpoint carries a synthetic-data footer.

## 4. Quick start (max 3 commands)

```bash
pip install -e ".[dev]" brickschema
make p18-run
streamlit run projects/p18-digital-twin-layer/src/explorer.py
```

`make p18-run` runs tests, builds crosswalk/relationships/Brick, computes coverage.

## 5. Results

Small profile, seed 42:

- **Canonical IDs**: 20,132 crosswalk rows across 8 systems (space_register, cafm, ifc, bms, meter, sensor, timetable, inspection)
- **Relationships**: 22,761 edges with 6 Brick predicates (`hasPart`, `isLocatedIn`, `feeds`, `hasPoint`, `isMeteredBy`, `isServedBy`)
- **Brick TTL**: Validated via `brickschema` SHACL; 5 SPARQL queries executable (AHU→spaces, CO₂ sensors, VAV boxes, etc.)
- **Coverage**: Assets with IFC GUID ~60%, Spaces with sensors ~6%, Assets linked to BMS ~78%, Meters mapped to building 100%
- **FastAPI**: 12 endpoints, API-key auth, OpenAPI docs at `/docs`
- **Explorer**: Building→Space→Asset tree, relationship graph, sensor trends, coverage report

## 6. Design decisions and trade-offs

- **Canonical IDs as URNs** (`space:S-B001-L00-001`) enable cross-system joins without a central registry.
- **Crosswalk is the single source of truth** for identity; relationships derive from it + gold marts.
- **Brick predicates are a pragmatic subset** (6 of ~200) chosen for HVAC/space/asset use cases; validation is via SHACL.
- **Asset IFC GUIDs are absent in warehouse** (only in truth parquet); coverage report surfaces this honestly.
- **BMS→asset mapping is synthetic** (by shared space); documented as such.
- **Time-series layer uses DuckDB directly** for simplicity; async FastAPI wraps it.

## 7. Data quality and testing approach

- `tests/test_p18.py`: 11 tests covering IDs, crosswalk, relationships, Brick generation/validation, SPARQL, coverage, orphan/ID-collision checks.
- Brick TTL validated via `brickschema` SHACL (passes).
- 5 SPARQL queries with expected-result assertions (e.g., AHU→spaces returns 33 rows).
- Coverage report computed from warehouse + truth parquet, surfacing known gaps (0% asset IFC in warehouse, 6% space sensor coverage).

## 8. Limitations and next steps with real data

- Asset IFC GUIDs missing from warehouse (only in truth parquet) → needs handover process (P12).
- BMS point→asset mapping is synthetic (space-based); needs real BMS export + asset register join.
- Brick model is one building (B001); extend to campus with `brick:Site` and `brick:Campus`.
- API auth is demo key only; real deployment needs OAuth2/OIDC.
- Time-series layer could add downsampling, interpolation, and caching.
- Explorer is Streamlit; real deployment might use React + Cytoscape.js or Three.js.

## 9. Skills demonstrated

E4 (canonical IDs, crosswalk, Brick schema), E6 (SHACL validation, SPARQL), D5 (FastAPI + OpenAPI, Streamlit), D6 (Brick Schema, semantic graph), D7 (time-series API, cross-system graph).

## 10. Outputs (built by `make p18-run`)

```
projects/p18-digital-twin-layer/outputs/
  entity_crosswalk.parquet / .csv      # 20,132 rows
  relationship.parquet / .csv          # 22,761 rows
  brick_B001.ttl                       # validated Brick TTL
  coverage.json                        # coverage report
```

## 11. Running the API and Explorer

```bash
# API (needs brickschema + fastapi + uvicorn)
uvicorn projects.p18-digital-twin-layer.src.api:app --host 0.0.0.0 --port 8000
# Docs: http://localhost:8000/docs

# Explorer
streamlit run projects/p18-digital-twin-layer/src/explorer.py
```