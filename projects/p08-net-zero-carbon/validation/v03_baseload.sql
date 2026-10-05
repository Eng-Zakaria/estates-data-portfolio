-- v03_baseload.sql — overnight baseload as % of daily peak per building (synthetic).
-- Overnight = minimum 00:00–05:00 London interval kW; peak = daily max kW.
-- kW = kWh per half hour × 2. Ties to: Power BI page 4 out-of-hours waste.
WITH hh AS (
    SELECT
        m.building_id,
        CAST(h.ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London' AS DATE) AS local_date,
        EXTRACT('hour' FROM h.ts_utc AT TIME ZONE 'UTC' AT TIME ZONE 'Europe/London') AS local_hour,
        h.value_kwh * 2.0 AS kw
    FROM main.fct_meter_hh AS h
    JOIN main.dim_meter AS m USING (meter_id)
    WHERE m.utility = 'electricity'
),
daily AS (
    SELECT
        building_id,
        local_date,
        MIN(CASE WHEN local_hour >= 0 AND local_hour < 5 THEN kw END) AS overnight_min_kw,
        MAX(kw) AS daily_peak_kw
    FROM hh
    GROUP BY 1, 2
)
SELECT
    building_id,
    COUNT(*) AS n_days,
    ROUND(AVG(overnight_min_kw), 2) AS avg_overnight_min_kw,
    ROUND(AVG(daily_peak_kw), 2) AS avg_daily_peak_kw,
    ROUND(AVG(overnight_min_kw) / NULLIF(AVG(daily_peak_kw), 0) * 100.0, 1) AS baseload_pct
FROM daily
GROUP BY 1
ORDER BY baseload_pct DESC;
