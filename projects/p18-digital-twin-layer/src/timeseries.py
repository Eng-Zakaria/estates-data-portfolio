"""Time-series access layer over gold marts (P18)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import duckdb


class TimeSeriesLayer:
    """Async time-series access over DuckDB gold marts."""

    def __init__(self, db_path: str = "data/warehouse.duckdb"):
        self.db_path = db_path

    def _connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(self.db_path, read_only=True)

    def meter_hh(
        self,
        meter_id: str,
        from_ts: datetime,
        to_ts: datetime,
        agg: str = "15min",
    ) -> list[dict]:
        """Half-hourly meter readings with optional aggregation."""
        con = self._connect()
        try:
            if agg == "15min":
                # Resample HH to 15min (interpolate)
                sql = """
                SELECT ts_utc, value_kwh
                FROM main.fct_meter_hh
                WHERE meter_id = ? AND ts_utc BETWEEN ? AND ?
                ORDER BY ts_utc
                """
            elif agg == "hour":
                sql = """
                SELECT date_trunc('hour', ts_utc) AS ts, SUM(value_kwh) AS value_kwh
                FROM main.fct_meter_hh
                WHERE meter_id = ? AND ts_utc BETWEEN ? AND ?
                GROUP BY 1 ORDER BY 1
                """
            elif agg == "day":
                sql = """
                SELECT date_trunc('day', ts_utc) AS ts, SUM(value_kwh) AS value_kwh
                FROM main.fct_meter_hh
                WHERE meter_id = ? AND ts_utc BETWEEN ? AND ?
                GROUP BY 1 ORDER BY 1
                """
            else:
                raise ValueError(f"Unknown agg: {agg}")
            return con.execute(sql, [meter_id, from_ts, to_ts]).fetchall()
        finally:
            con.close()

    def sensor_15min(
        self,
        sensor_id: str,
        from_ts: datetime,
        to_ts: datetime,
        agg: str = "15min",
    ) -> list[dict]:
        """Sensor 15-min readings with optional aggregation."""
        con = self._connect()
        try:
            if agg == "15min":
                sql = """
                SELECT ts_utc, observed_count AS value
                FROM main.fct_space_observed_occupancy
                WHERE sensor_id = ? AND ts_utc BETWEEN ? AND ?
                ORDER BY ts_utc
                """
            elif agg == "hour":
                sql = """
                SELECT date_trunc('hour', ts_utc) AS ts, AVG(observed_count) AS value
                FROM main.fct_space_observed_occupancy
                WHERE sensor_id = ? AND ts_utc BETWEEN ? AND ?
                GROUP BY 1 ORDER BY 1
                """
            elif agg == "day":
                sql = """
                SELECT date_trunc('day', ts_utc) AS ts, AVG(observed_count) AS value
                FROM main.fct_space_observed_occupancy
                WHERE sensor_id = ? AND ts_utc BETWEEN ? AND ?
                GROUP BY 1 ORDER BY 1
                """
            else:
                raise ValueError(f"Unknown agg: {agg}")
            return con.execute(sql, [sensor_id, from_ts, to_ts]).fetchall()
        finally:
            con.close()

    def bms_trends(
        self,
        point_id: str,
        from_ts: datetime,
        to_ts: datetime,
    ) -> list[dict]:
        """BMS trend readings (no aggregation)."""
        con = self._connect()
        try:
            sql = """
            SELECT ts_utc, value
            FROM main.stg_bms__trend
            WHERE point_id = ? AND ts_utc BETWEEN ? AND ?
            ORDER BY ts_utc
            """
            return con.execute(sql, [point_id, from_ts, to_ts]).fetchall()
        finally:
            con.close()

    def latest_readings(self, limit: int = 100) -> list[dict]:
        """Latest readings across all sensors/meters."""
        con = self._connect()
        try:
            sql = """
            SELECT 'meter' AS source, meter_id AS id, ts_utc, value_kwh AS value
            FROM main.fct_meter_hh
            WHERE ts_utc = (SELECT MAX(ts_utc) FROM main.fct_meter_hh)
            UNION ALL
            SELECT 'sensor' AS source, sensor_id AS id, ts_utc, observed_count AS value
            FROM main.fct_space_observed_occupancy
            WHERE ts_utc = (SELECT MAX(ts_utc) FROM main.fct_space_observed_occupancy)
            UNION ALL
            SELECT 'bms' AS source, point_id AS id, ts_utc, value
            FROM main.stg_bms__trend
            WHERE ts_utc = (SELECT MAX(ts_utc) FROM main.stg_bms__trend)
            LIMIT ?
            """
            return con.execute(sql, [limit]).fetchall()
        finally:
            con.close()


if __name__ == "__main__":
    import asyncio
    from datetime import datetime, timedelta

    ts = TimeSeriesLayer()
    now = datetime(2026, 3, 31, 12, 0, 0)
    print("Meter HH (1 hour):", ts.meter_hh("M-B001-E01", now - timedelta(hours=1), now)[:3])
    print("Sensor 15min (1 hour):", ts.sensor_15min("SN-0001", now - timedelta(hours=1), now)[:3])
    print("BMS trends (1 hour):", ts.bms_trends("SN-0001 [ppm]", now - timedelta(hours=1), now)[:3])
    print("Latest readings:", ts.latest_readings(5))