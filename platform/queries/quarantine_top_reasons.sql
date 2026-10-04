-- Quarantine top reasons (DuckDB). Athena: same with table names.
SELECT _reject_reason, COUNT(*) AS n
FROM read_parquet('data/lakehouse/quarantine/cafm_workorders/quarantine.parquet')
GROUP BY 1 ORDER BY n DESC LIMIT 20;
