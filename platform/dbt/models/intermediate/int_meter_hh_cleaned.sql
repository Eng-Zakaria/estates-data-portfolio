WITH hh_a AS (
    SELECT meter_id, ts_utc, value_kwh FROM {{ ref('stg_meter__hh_a') }}
),

hh_b AS (
    SELECT meter_id, ts_utc, value_kwh FROM {{ ref('stg_meter__hh_b') }}
),

unioned AS (
    SELECT * FROM hh_a
    UNION ALL
    SELECT * FROM hh_b
),

cleaned AS (
    SELECT
        meter_id,
        CAST(ts_utc AS TIMESTAMPTZ) AS ts_utc,
        CAST(value_kwh AS DOUBLE) AS value_kwh,
        {{ uk_local_ts('ts_utc') }} AS ts_local,
        {{ is_working_hours('ts_utc') }} AS is_working_hours
    FROM unioned
    -- P05 prerequisite note: exclude far-future planted defects (synthetic window
    -- ends 2026-03-31; rows dated 2099 fail P01 quarantine and must not reach marts).
    WHERE CAST(ts_utc AS TIMESTAMPTZ) < CAST('2027-01-01' AS TIMESTAMPTZ)
)

SELECT * FROM cleaned
