-- v04_planted_checks.sql — do the planted faults land where the spec requires?
-- Ties to: README section 5.2 and the drill-through evidence page.
--
-- Expected (seed 7):
--   M-B007-E01  rank 1, overnight_ratio >= 0.55 (planted fault = 0.6 of peak)
--   M-B019-G01  rank 2 (planted summer heating fault)
--   M-B015-E01  flatline label present and gbp_year = 0 (use cannot be estimated)
WITH readings AS (
    SELECT r.meter_id, m.building_id, m.utility, r.ts_utc, r.value
    FROM read_parquet('data/truth/meter_readings_hh.parquet') AS r
    JOIN read_parquet('data/truth/meters.parquet') AS m USING (meter_id)
    UNION ALL
    SELECT r.meter_id, m.building_id, m.utility, r.ts_utc, r.value
    FROM read_parquet('data/p16_default/meter_readings_hh.parquet') AS r
    JOIN read_parquet('data/p16_default/meters.parquet') AS m USING (meter_id)
    WHERE m.meter_id IN ('M-B019-G01', 'M-B015-E01')
),
overnight AS (
    SELECT
        meter_id,
        MAX(peak) AS peak,
        AVG(value) FILTER (WHERE hod < 5) AS night_mean
    FROM (
        SELECT
            meter_id,
            value,
            EXTRACT(hour FROM ts_utc) AS hod,
            quantile_cont(value, 0.99) OVER (PARTITION BY meter_id) AS peak
        FROM readings
        WHERE meter_id IN ('M-B007-E01', 'M-B015-E01')
    )
    GROUP BY 1
),
board AS (
    SELECT
        ROW_NUMBER() OVER (ORDER BY gbp_year DESC) AS rank,
        meter_id,
        building,
        types,
        gbp_year
    FROM read_parquet('projects/p16-energy-anomaly/outputs/building_scorecard.parquet')
)
SELECT
    b.rank,
    b.meter_id,
    b.building,
    b.types,
    b.gbp_year,
    ROUND(o.night_mean / NULLIF(o.peak, 0), 3) AS overnight_ratio,
    CASE
        WHEN b.meter_id = 'M-B007-E01'
             AND o.night_mean / NULLIF(o.peak, 0) >= 0.55
             AND b.rank = 1
            THEN 'PASS planted overnight fault, rank 1'
        WHEN b.meter_id = 'M-B019-G01' AND b.rank = 2
            THEN 'PASS planted summer heating, rank 2'
        WHEN b.meter_id = 'M-B015-E01'
             AND CONTAINS(b.types, 'flatline')
             AND b.gbp_year = 0
            THEN 'PASS planted flatline, GBP 0 by design'
        ELSE 'check'
    END AS acceptance
FROM board AS b
LEFT JOIN overnight AS o USING (meter_id)
WHERE b.meter_id IN ('M-B007-E01', 'M-B019-G01', 'M-B015-E01')
ORDER BY b.rank;