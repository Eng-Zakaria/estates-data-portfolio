WITH hh AS (
    SELECT * FROM {{ ref('fct_meter_hh') }}
),

weather AS (
    SELECT
        CAST(CAST(ts_utc AS DATE) AS DATE) AS weather_date,
        SUM(hdd_base15_5) AS hdd
    FROM {{ ref('stg_truth__weather') }}
    GROUP BY 1
),

daily AS (
    SELECT
        meter_id,
        building_id,
        utility,
        CAST(ts_utc AS DATE) AS energy_date,
        SUM(value_kwh) AS kwh,
        MAX(value_kwh) AS peak_half_hour_kwh,
        COUNT(*) AS n_periods
    FROM hh
    GROUP BY 1, 2, 3, 4
)

SELECT
    d.meter_id,
    d.building_id,
    d.utility,
    d.energy_date,
    d.kwh,
    d.peak_half_hour_kwh,
    d.n_periods,
    COALESCE(w.hdd, 0.0) AS hdd
FROM daily AS d
LEFT JOIN weather AS w ON w.weather_date = d.energy_date
