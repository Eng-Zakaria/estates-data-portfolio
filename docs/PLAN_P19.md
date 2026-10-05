# PLAN: P19 Spatial analysis and carbon map

## Goal
Campus-scale spatial analytics on public OSM geometry + synthetic P04/P08
metrics: footprint sanity, carbon choropleth, heat-cluster screening,
walking isochrones, OGC outputs + Power BI map handoff.

## Why P19 now
Explicitly requested. Free territory (`projects/p19-spatial-carbon-map/`);
gold + P08 marts stable. Network verified (OSM fetch works: 1,912 raw
footprints in test bbox).

## Key decisions (spec-driven)
- Geometry: OSM buildings, bbox default Univ. of Exeter Streatham
  (50.736, -3.534, dist 800m) configurable; names anonymised
  (Building A...); synth IDs B001–B008 by **area-rank match** (largest
  footprint ↔ largest GIA). Attribution OSM contributors, ODbL → DATA.md.
- Filter: keep non-residential footprints (drop house/garage/shed/
  residential), valid non-empty Polygon/MultiPolygon only; explode
  multipolygons for area ranking.
- CRS: EPSG:27700 for area/distance; export EPSG:4326. Tests offline
  (known square → 10,000 m²; known-point distances).
- Isochrones: osmnx walk network cached in `data/`; 400m/800m ≈ 5/10 min
  at 4.8 km/h from the largest building; reachable-node union.
- Outputs: GeoPackage, GeoJSON, TopoJSON (`topojson` lib), PNGs,
  Folium HTML, `.qml` stretch, PBI map-page handoff (TopoJSON Shape Map
  + lat/long fallback). `make p19` = fetch (cached) + build.

## Tasks
1. `requirements.txt` (pinned-ish spatial stack) + README install line —
   no shared-file edits except Makefile/`DATA.md`/`STATUS.md`.
2. `scripts/fetch_osm.py` (bbox in/out config, cache, retrieval log).
3. `src/spatial.py`: clean, project, areas, implied storeys + outlier flag,
   area-rank assignment, centroid distance matrix, threshold clustering +
   gas sums, choropleth breaks, isochrone polygons from edge lengths.
4. `scripts/build_outputs.py`: all artefacts + PBI handoff.
5. `tests/`: validity/empty, CRS area fixture, distance fixture,
   assignment determinism, storey-flag logic, exports exist (no network).
6. `README.md` (CRS decisions, limits, attribution), `SPEC.md`,
   `make p19`, DATA.md, STATUS.md, commit.

## Risks
- OSMnx/Overpass flakiness → cache + retry once; build works from cache.
- QML hand-written: keep minimal, validate XML parses.
- Warehouse drift (concurrent session): read gold at build time, record
  row counts/dates in outputs log.

## Open questions
- None blocking. Streatham chosen as thematically apt default; any campus
  bbox works via `--bbox`.
