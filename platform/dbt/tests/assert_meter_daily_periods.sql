WITH daily AS (
    SELECT
        meter_id,
        CAST(TIMEZONE('Europe/London', ts_utc) AS DATE) AS local_date,
        COUNT(DISTINCT ts_utc) AS periods
    FROM {{ ref('fct_meter_hh') }}
    GROUP BY 1, 2
),

expected AS (
    SELECT
        *,
        CASE
            WHEN local_date IN (DATE '2026-03-29', DATE '2024-03-31', DATE '2025-03-30') THEN 46
            WHEN local_date IN (DATE '2024-10-27', DATE '2025-10-26', DATE '2026-10-25') THEN 50
            ELSE 48
        END AS expected_periods
    FROM daily
)

SELECT meter_id, local_date, periods, expected_periods
FROM expected
WHERE periods > expected_periods
