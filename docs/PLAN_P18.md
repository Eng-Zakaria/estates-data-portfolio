# PLAN: P18 Digital twin data layer

## Goal
Build the data foundation of a campus digital twin: canonical IDs, cross-system
crosswalk, Brick-aligned relationship graph, time-series access layer, FastAPI
API, and explorer UI. Degrades gracefully when sources (IFC, BMS) are sparse.

## Why P18 now
Next free item. Dependencies stable: P04 gold marts + truth parquet (IFC GUIDs)
all available. Fresh `projects/p18-digital-twin-layer/` tree.

## Key facts (measured 2026-10-06, small profile seed 42)
- 8 buildings, 495 spaces (327 have IFC GUIDs), 1496 assets (0 with IFC GUIDs),
  16 meters, 90 sensors, 5938 work orders, 40 inspections.
- BMS trends: 90 sensors, point_id format "SN-XXXX [ppm/°C/%]".
- fct_meter_hh: 67,822 rows; fct_sensor_15min: 773,974 rows.
- IFC GUIDs: spaces have them in truth (327/495), assets have column but all NULL.
- No native BMS point → asset/space mapping; will need synthetic mapping.

## Tasks
1. `src/ids.py`: canonical ID prefixes + generator/validation.
2. `src/crosswalk.py`: build `entity_crosswalk` (canonical_id, system,
   native_id) from gold + truth (space register, CAFM, IFC, BMS point,
   meter, sensor). Deterministic, versioned CSV + Parquet.
3. `src/relationships.py`: build `relationship` (subject, predicate,
   object, source, valid_from, valid_to) with Brick predicates:
   `hasPart`, `isLocatedIn`, `feeds`, `hasPoint`, `isMeteredBy`, `isServedBy`.
   Deterministic from gold + crosswalk + synthetic BMS mapping.
4. `src/timeseries.py`: time-series access layer over `fct_meter_hh`,
   `fct_sensor_15min`, `stg_bms__trend` via DuckDB; async FastAPI endpoints.
5. `src/brick.py`: generate Brick TTL for one building (B001): AHU system
   → terminal units → spaces; points (temp, damper, CO2). Validate with
   `brickschema` (SHACL). Provide ≥5 SPARQL queries + expected results tests.
6. `src/api.py`: FastAPI with OpenAPI:
   `/buildings`, `/buildings/{id}/spaces`, `/spaces/{id}` (assets,
   sensors, meters, latest readings, open work orders, inspections),
   `/assets/{id}/timeseries`, `/graph/neighbors/{id}`, `/coverage`.
   Pagination, API-key header (demo key via `.env`), consistent error model,
   `TestClient` tests, Dockerfile.
7. `src/explorer.py`: Streamlit explorer (Building → space → asset tree;
   relationship graph; AHU click → served spaces + sensor trend).
8. `src/coverage.py`: twin_coverage report (% assets with IFC GUID,
   % spaces with sensors, % assets linked to BMS point, % meters mapped).
9. Tests: graph traversal (AHU → spaces), API endpoints, Brick validation,
   SPARQL expected results, coverage numbers, orphan/ID-collision tests.
10. README, SPEC, make p18-run, STATUS.md, commit.

## Risks
- `brickschema` API may differ from memory → verify empirically first.
- BMS point → asset/space mapping is synthetic; document clearly.
- Asset IFC GUIDs all NULL; coverage will show 0% honestly.
- Warehouse lock contention → read-only connections + retry.

## Open questions
- None blocking. P11 (IFC analytics) not yet built; P18 uses truth
  parquet directly. P15/P17 not built; BMS mapping is synthetic.