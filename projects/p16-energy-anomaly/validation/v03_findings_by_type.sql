-- v03_findings_by_type.sql — fault-type counts behind the donut chart.
-- Ties to: page 1 donut (fct_finding exploded from the comma-joined `types`).
--
-- The scorecard stores types as one comma-joined string; Power Query splits it.
-- This script does the same split in SQL so the donut can be tied out:
--
-- Expected (seed 7, 18 meters): step_change and spike dominate; flatline on
-- M-B015-E01, missing_data where the series has gaps. Exact counts come from
-- the query result at build time; the check is that the donut total equals the
-- number of comma-separated labels in `types`.
WITH exploded AS (
    SELECT
        meter_id,
        building,
        TRIM(unnest(STRING_SPLIT(types, ','))) AS type
    FROM read_parquet('projects/p16-energy-anomaly/outputs/building_scorecard.parquet')
    WHERE types IS NOT NULL AND types <> ''
)
SELECT
    type,
    COUNT(*) AS findings,
    COUNT(DISTINCT meter_id) AS meters,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_findings
FROM exploded
GROUP BY 1
ORDER BY findings DESC;