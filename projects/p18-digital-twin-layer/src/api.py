"""FastAPI REST API for the digital twin data layer (P18).

Endpoints:
- /buildings
- /buildings/{id}/spaces
- /spaces/{id} (assets, sensors, meters, latest readings, open work orders, inspections)
- /assets/{id}/timeseries?from&to&agg=15min|hour|day
- /graph/neighbors/{id}?depth=2
- /coverage

Pagination, API-key header (demo key via .env), consistent error model.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# Load demo API key from env
DEMO_API_KEY = os.getenv("P18_API_KEY", "p18-demo-key-change-in-prod")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)) -> str:
    if api_key != DEMO_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key


app = FastAPI(
    title="Estates Digital Twin API",
    version="0.1.0",
    description="Data foundation for campus digital twin (synthetic data)",
    dependencies=[Depends(verify_api_key)],
)

# Import our data access layers
from .timeseries import TimeSeriesLayer
from .crosswalk import load_crosswalk, build_crosswalk
from .relationships import build_relationships
from .brick import generate_brick_ttl, validate_brick, run_sparql_queries
from .coverage import compute_coverage


ts_layer = TimeSeriesLayer()


# --- Pydantic Models ---
class BuildingOut(BaseModel):
    building_id: str
    building_name: str
    campus: str
    gia_m2: float
    nia_m2: float
    n_floors: int
    year_built: int
    primary_use: str
    heating_fuel: str
    epc_band: str


class SpaceOut(BaseModel):
    space_id: str
    building_id: str
    space_category: str
    nia_m2: float
    capacity_seats: int
    building_name: str
    campus: str
    gia_m2: float


class AssetOut(BaseModel):
    asset_id: str
    building_id: str
    space_id: str
    asset_type: str
    install_date: str
    expected_life_years: int
    condition_grade: str
    criticality: int
    replacement_cost_gbp: float


class SensorOut(BaseModel):
    sensor_id: str
    space_id: str
    sensor_type: str
    install_date: str


class MeterOut(BaseModel):
    meter_id: str
    building_id: str
    utility: str
    meter_role: str
    parent_meter_id: Optional[str]
    unit: str


class TimeseriesPoint(BaseModel):
    ts: datetime
    value: float


class AssetTimeseriesOut(BaseModel):
    asset_id: str
    sensor_type: str
    points: list[TimeseriesPoint]


class NeighborsOut(BaseModel):
    canonical_id: str
    depth: int
    neighbors: list[dict]


class CoverageOut(BaseModel):
    assets_with_ifc_guid_pct: float
    spaces_with_sensors_pct: float
    assets_linked_to_bms_pct: float
    meters_mapped_to_building_pct: float


class ErrorOut(BaseModel):
    detail: str


# --- Exception Handlers ---
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# --- Endpoints ---
@app.get("/buildings", response_model=list[BuildingOut], tags=["Buildings"])
async def list_buildings(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        rows = con.execute(
            "SELECT * FROM main.dim_building LIMIT ? OFFSET ?", [limit, offset]
        ).fetchall()
        cols = [d[0] for d in con.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


@app.get("/buildings/{building_id}/spaces", response_model=list[SpaceOut], tags=["Buildings"])
async def building_spaces(
    building_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        rows = con.execute(
            "SELECT * FROM main.dim_space WHERE building_id = ? LIMIT ? OFFSET ?",
            [building_id, limit, offset],
        ).fetchall()
        cols = [d[0] for d in con.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


@app.get("/spaces/{space_id}", response_model=SpaceOut, tags=["Spaces"])
async def get_space(space_id: str):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        row = con.execute(
            "SELECT * FROM main.dim_space WHERE space_id = ?", [space_id]
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Space not found")
        cols = [d[0] for d in con.description]
        return dict(zip(cols, row))
    finally:
        con.close()


@app.get("/spaces/{space_id}/assets", response_model=list[AssetOut], tags=["Spaces"])
async def space_assets(
    space_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        rows = con.execute(
            "SELECT * FROM main.dim_asset WHERE space_id = ? LIMIT ? OFFSET ?",
            [space_id, limit, offset],
        ).fetchall()
        cols = [d[0] for d in con.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


@app.get("/spaces/{space_id}/sensors", response_model=list[SensorOut], tags=["Spaces"])
async def space_sensors(space_id: str):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        rows = con.execute(
            "SELECT sensor_id, space_id, sensor_type, install_date FROM main.stg_truth__sensor WHERE space_id = ?",
            [space_id],
        ).fetchall()
        cols = [d[0] for d in con.description]
        return [dict(zip(cols, r)) for r in rows]
    finally:
        con.close()


@app.get("/spaces/{space_id}/readings", tags=["Spaces"])
async def space_latest_readings(space_id: str):
    """Latest sensor readings for a space."""
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        # Get sensors in space
        sensors = con.execute(
            "SELECT sensor_id, sensor_type FROM main.stg_truth__sensor WHERE space_id = ?",
            [space_id],
        ).fetchall()
        if not sensors:
            return {"space_id": space_id, "readings": []}

        results = []
        for sensor_id, sensor_type in sensors:
            row = con.execute(
                """
                SELECT ts_utc, observed_count
                FROM main.fct_space_observed_occupancy
                WHERE sensor_id = ?
                ORDER BY ts_utc DESC LIMIT 1
                """,
                [sensor_id],
            ).fetchone()
            if row:
                results.append({
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "ts_utc": row[0],
                    "value": row[1],
                })
        return {"space_id": space_id, "readings": results}
    finally:
        con.close()


@app.get("/assets/{asset_id}", response_model=AssetOut, tags=["Assets"])
async def get_asset(asset_id: str):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        row = con.execute(
            "SELECT * FROM main.dim_asset WHERE asset_id = ?", [asset_id]
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Asset not found")
        cols = [d[0] for d in con.description]
        return dict(zip(cols, row))
    finally:
        con.close()


@app.get("/assets/{asset_id}/timeseries", response_model=AssetTimeseriesOut, tags=["Assets"])
async def asset_timeseries(
    asset_id: str,
    from_ts: datetime = Query(..., description="Start timestamp (ISO 8601)"),
    to_ts: datetime = Query(..., description="End timestamp (ISO 8601)"),
    agg: str = Query("15min", pattern="^(15min|hour|day)$"),
):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        # Get sensors linked to this asset (via space)
        sensors = con.execute(
            """
            SELECT s.sensor_id, s.sensor_type
            FROM main.stg_truth__sensor s
            JOIN main.dim_asset a ON a.space_id = s.space_id
            WHERE a.asset_id = ?
            """,
            [asset_id],
        ).fetchall()

        all_points = []
        for sensor_id, sensor_type in sensors:
            if agg == "15min":
                sql = """
                SELECT ts_utc, observed_count
                FROM main.fct_space_observed_occupancy
                WHERE sensor_id = ? AND ts_utc BETWEEN ? AND ?
                ORDER BY ts_utc
                """
            elif agg == "hour":
                sql = """
                SELECT date_trunc('hour', ts_utc) AS ts, AVG(observed_count)
                FROM main.fct_space_observed_occupancy
                WHERE sensor_id = ? AND ts_utc BETWEEN ? AND ?
                GROUP BY 1 ORDER BY 1
                """
            elif agg == "day":
                sql = """
                SELECT date_trunc('day', ts_utc) AS ts, AVG(observed_count)
                FROM main.fct_space_observed_occupancy
                WHERE sensor_id = ? AND ts_utc BETWEEN ? AND ?
                GROUP BY 1 ORDER BY 1
                """
            else:
                raise HTTPException(status_code=400, detail="Invalid agg")

            points = con.execute(sql, [sensor_id, from_ts, to_ts]).fetchall()
            return {
                "asset_id": asset_id,
                "sensor_type": "aggregated",
                "points": [{"ts": p[0], "value": p[1]} for p in points],
            }
    finally:
        con.close()


@app.get("/meters/{meter_id}", response_model=MeterOut, tags=["Meters"])
async def get_meter(meter_id: str):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        row = con.execute(
            "SELECT * FROM main.dim_meter WHERE meter_id = ?", [meter_id]
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meter not found")
        cols = [d[0] for d in con.description]
        return dict(zip(cols, row))
    finally:
        con.close()


@app.get("/graph/neighbors/{canonical_id}", response_model=NeighborsOut, tags=["Graph"])
async def graph_neighbors(
    canonical_id: str,
    depth: int = Query(2, ge=1, le=3),
):
    import duckdb
    con = duckdb.connect("data/warehouse.duckdb", read_only=True)
    try:
        # Load relationships from our built file or build on demand
        # For now, use the relationships we built
        rels = build_relationships()
        # BFS up to depth
        visited = {canonical_id}
        frontier = {canonical_id}
        neighbors = []

        for d in range(depth):
            next_frontier = set()
            for node in frontier:
                edges = con.execute(
                    "SELECT subject_id, predicate, object_id FROM read_parquet('projects/p18-digital-twin-layer/outputs/relationship.parquet') WHERE subject_id = ? OR object_id = ?",
                    [canonical_id, canonical_id],
                ).fetchall()
                for subj, pred, obj in edges:
                    neighbor = obj if subj == canonical_id else subj
                    if neighbor not in visited:
                        visited.add(neighbor)
                        next_frontier.add(neighbor)
                        neighbors.append({
                            "from": subj,
                            "predicate": pred,
                            "to": obj,
                            "direction": "out" if subj == canonical_id else "in",
                        })
            canonical_id = next_frontier.pop() if next_frontier else None
            if not canonical_id:
                break
        return {"canonical_id": canonical_id, "depth": depth, "neighbors": neighbors}
    finally:
        con.close()


@app.get("/coverage", response_model=CoverageOut, tags=["Coverage"])
async def get_coverage():
    from .coverage import compute_coverage
    return compute_coverage()


# --- Brick / SPARQL ---
@app.get("/brick/{building_id}.ttl", tags=["Brick"])
async def get_brick_ttl(building_id: str):
    from pathlib import Path
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl(building_id, Path("projects/p18-digital-twin-layer/outputs"))
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(ttl, media_type="text/turtle")


@app.get("/brick/{building_id}/validate", tags=["Brick"])
async def validate_brick_model(building_id: str):
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl(building_id, out)
    valid, errors = validate_brick(ttl)
    return {"valid": valid, "errors": errors}


@app.post("/brick/{building_id}/sparql", tags=["Brick"])
async def run_sparql(building_id: str, query: str):
    out = Path("projects/p18-digital-twin-layer/outputs")
    ttl = generate_brick_ttl(building_id, out)
    from .brick import run_sparql_queries
    results = run_sparql_queries(query)
    return results


# --- Health ---
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)