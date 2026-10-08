-- v01_action_list.sql — ranked overnight-excess list (synthetic campus).
-- Ties to: page 1 bar chart (top meters by £/yr) and the KPI cards.
--
-- P16's parquet outputs are produced by the pipeline; this script re-derives the
-- overnight component straight from the truth data so the Power BI numbers are
-- checked against something other than the pipeline echoing itself.
--
-- Run with DuckDB: duckdb -c ".read projects/p16-energy-anomaly/validation/v01_action_list.sql"
--
-- Expected (seed 7): M-B007-E01 is the only meter with a material overnight
-- excess, overnight_ratio >= 0.55, overnight_gbp_year in the thousands.
WITH readings AS (
    SELECT r.meter_id, m.building_id, m.utility, r.ts_utc, r.value
    FROM read_parquet('data/truth/meter_readings_hh.parquet') AS r
    JOIN read_parquet('data/truth/meters.parquet') AS m USING (meter_id)
    WHERE m.utility IN ('electricity', 'gas')
    UNION ALL
    SELECT r.meter_id, m.building_id, m.utility, r.ts_utc, r.value
    FROM read_parquet('data/p16_default/meter_readings_hh.parquet') AS r
    JOIN read_parquet('data/p16_default/meters.parquet') AS m USING (meter_id)
    WHERE m.utility IN ('electricity', 'gas')
      AND m.meter_id IN ('M-B019-G01', 'M-B015-E01')
),
with_peak AS (
    SELECT
        meter_id,
        building_id,
        utility,
        value,
        EXTRACT(hour FROM ts_utc) AS hod,
        quantile_cont(value, 0.99) OVER (PARTITION BY meter_id) AS peak
    FROM readings
),
night AS (
    SELECT
        meter_id,
        building_id,
        utility,
        MAX(peak) AS peak,
        AVG(value) FILTER (WHERE hod < 5) AS night_mean,
        5.0 * GREATEST(AVG(value) FILTER (WHERE hod < 5) - 0.2 * MAX(peak), 0) AS overnight_excess_kwh_day
    FROM with_peak
    GROUP BY 1, 2, 3
)
SELECT
    meter_id,
    building_id,
    utility,
    ROUND(peak, 2) AS peak_kwh_period,
    ROUND(night_mean / NULLIF(peak, 0), 3) AS overnight_ratio,
    ROUND(overnight_excess_kwh_day, 2) AS overnight_excess_kwh_day,
    ROUND(overnight_excess_kwh_day * 365, 1) AS overnight_kwh_year,
    ROUND(overnight_excess_kwh_day * 365 * 0.28, 2) AS overnight_gbp_year
FROM night
WHERE overnight_excess_kwh_day > 0
ORDER BY overnight_gbp_year DESC;