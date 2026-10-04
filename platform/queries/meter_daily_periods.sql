-- Daily HH periods per meter (expect 48; 46 spring-forward, 50 autumn-back).
-- DuckDB: timezone('Europe/London', ts_utc). Athena: use at_timezone().
SELECT meter_id,
  CAST(timezone('Europe/London', ts_utc) AS DATE) AS local_date,
  COUNT(DISTINCT ts_utc) AS periods
FROM read_parquet('data/lakehouse/silver/meter_hh_supplierA/silver.parquet')
GROUP BY 1, 2 ORDER BY 1, 2 LIMIT 50;
