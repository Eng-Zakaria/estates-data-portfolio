"""P17 data loading from foundation truth (synthetic)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import duckdb
import pandas as pd

from .config import get_settings


def _con() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(":memory:")


def load_sensors(truth_dir: Path | None = None) -> pd.DataFrame:
    """Load sensor registry (SN-XXXX, space_id, sensor_type, install_date)."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(
            f"SELECT sensor_id, space_id, sensor_type, install_date FROM '{truth_dir / 'sensors.parquet'}'"
        ).df()
    finally:
        con.close()
    df["install_date"] = pd.to_datetime(df["install_date"])
    return df


def load_readings(
    sensor_ids: list[str] | None = None,
    sensor_type: Literal["co2", "temp", "occupancy_count"] | None = None,
    start_ts: str | None = None,
    end_ts: str | None = None,
    truth_dir: Path | None = None,
) -> pd.DataFrame:
    """Load sensor readings with optional filters. Returns ts_utc, sensor_id, value."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        where = []
        params = []
        if sensor_ids:
            placeholders = ",".join(["?"] * len(sensor_ids))
            where.append(f"sensor_id IN ({placeholders})")
            params.extend(sensor_ids)
        if sensor_type:
            # join with sensors table to filter by type
            where.append("s.sensor_type = ?")
            params.append(sensor_type)
        if start_ts:
            where.append("ts_utc >= ?")
            params.append(start_ts)
        if end_ts:
            where.append("ts_utc <= ?")
            params.append(end_ts)

        where_clause = "WHERE " + " AND ".join(where) if where else ""
        join_clause = "JOIN 'data/truth/sensors.parquet' s ON r.sensor_id = s.sensor_id" if sensor_type else ""

        sql = f"""
            SELECT r.ts_utc, r.sensor_id, r.value
            FROM '{truth_dir / 'sensor_readings.parquet'}' r
            {join_clause}
            {where_clause}
            ORDER BY r.sensor_id, r.ts_utc
        """
        df = con.execute(sql, params).df()
    finally:
        con.close()

    if not df.empty:
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


def load_spaces(truth_dir: Path | None = None) -> pd.DataFrame:
    """Load space register (space_id, building_id, space_category, nia_m2, capacity_seats)."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(
            f"SELECT space_id, building_id, space_category, nia_m2, capacity_seats FROM '{truth_dir / 'spaces.parquet'}'"
        ).df()
    finally:
        con.close()
    return df


def load_timetable(truth_dir: Path | None = None) -> pd.DataFrame:
    """Load timetable events (event_id, space_id, start_ts, end_ts, module_code, department_id, group_size, booked_capacity_need)."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(
            f"SELECT event_id, space_id, start_ts, end_ts, module_code, department_id, group_size, booked_capacity_need FROM '{truth_dir / 'timetable_events.parquet'}'"
        ).df()
    finally:
        con.close()
    return df


def load_buildings(truth_dir: Path | None = None) -> pd.DataFrame:
    """Load building register (building_id, building_name, campus, gia_m2, primary_use)."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(
            f"SELECT building_id, building_name, campus, gia_m2, primary_use FROM '{truth_dir / 'buildings.parquet'}'"
        ).df()
    finally:
        con.close()
    return df


def load_all_co2_readings(truth_dir: Path | None = None) -> pd.DataFrame:
    """Convenience: all CO2 readings with space context."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(f"""
            SELECT r.ts_utc, r.sensor_id, r.value, s.space_id, sp.building_id, s.sensor_type
            FROM '{truth_dir / 'sensor_readings.parquet'}' r
            JOIN '{truth_dir / 'sensors.parquet'}' s ON r.sensor_id = s.sensor_id
            JOIN '{truth_dir / 'spaces.parquet'}' sp ON s.space_id = sp.space_id
            WHERE s.sensor_type = 'co2'
            ORDER BY r.sensor_id, r.ts_utc
        """).df()
    finally:
        con.close()
    if not df.empty:
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


def load_all_temp_readings(truth_dir: Path | None = None) -> pd.DataFrame:
    """Convenience: all temperature readings with space context."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(f"""
            SELECT r.ts_utc, r.sensor_id, r.value, s.space_id, sp.building_id, s.sensor_type
            FROM '{truth_dir / 'sensor_readings.parquet'}' r
            JOIN '{truth_dir / 'sensors.parquet'}' s ON r.sensor_id = s.sensor_id
            JOIN '{truth_dir / 'spaces.parquet'}' sp ON s.space_id = sp.space_id
            WHERE s.sensor_type = 'temp'
            ORDER BY r.sensor_id, r.ts_utc
        """).df()
    finally:
        con.close()
    if not df.empty:
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


def load_all_occupancy_readings(truth_dir: Path | None = None) -> pd.DataFrame:
    """Convenience: all occupancy count readings with space context."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(f"""
            SELECT r.ts_utc, r.sensor_id, r.value, s.space_id, sp.building_id, s.sensor_type
            FROM '{truth_dir / 'sensor_readings.parquet'}' r
            JOIN '{truth_dir / 'sensors.parquet'}' s ON r.sensor_id = s.sensor_id
            JOIN '{truth_dir / 'spaces.parquet'}' sp ON s.space_id = sp.space_id
            WHERE s.sensor_type = 'occupancy_count'
            ORDER BY r.sensor_id, r.ts_utc
        """).df()
    finally:
        con.close()
    if not df.empty:
        df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    return df


def load_all_sensor_metadata(truth_dir: Path | None = None) -> pd.DataFrame:
    """All sensors with space/building context."""
    truth_dir = truth_dir or get_settings().truth_dir
    con = _con()
    try:
        df = con.execute(f"""
            SELECT s.sensor_id, s.space_id, s.sensor_type, s.install_date,
                   sp.building_id, sp.space_category, sp.nia_m2, sp.capacity_seats
            FROM '{truth_dir / 'sensors.parquet'}' s
            JOIN '{truth_dir / 'spaces.parquet'}' sp ON s.space_id = sp.space_id
        """).df()
    finally:
        con.close()
    if not df.empty:
        df["install_date"] = pd.to_datetime(df["install_date"])
    return df