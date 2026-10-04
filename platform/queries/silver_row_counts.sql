-- Silver row counts per source (DuckDB). Athena: replace read_parquet with table names.
SELECT 'space_register' AS source, COUNT(*) AS silver_rows FROM read_parquet('data/lakehouse/silver/space_register/silver.parquet')
UNION ALL SELECT 'cafm_workorders', COUNT(*) FROM read_parquet('data/lakehouse/silver/cafm_workorders/silver.parquet')
UNION ALL SELECT 'meter_A', COUNT(*) FROM read_parquet('data/lakehouse/silver/meter_hh_supplierA/silver.parquet')
UNION ALL SELECT 'meter_B', COUNT(*) FROM read_parquet('data/lakehouse/silver/meter_hh_supplierB/silver.parquet')
UNION ALL SELECT 'sensors', COUNT(*) FROM read_parquet('data/lakehouse/silver/sensors/silver.parquet');
