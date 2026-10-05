{{ config(
    materialized='incremental',
    unique_key=['meter_id', 'ts_utc'],
    incremental_strategy='delete+insert',
    on_schema_change='append_new_columns'
) }}

WITH cleaned AS (
    SELECT * FROM {{ ref('int_meter_hh_cleaned') }}
    {% if is_incremental() %}
    WHERE ts_utc >= (SELECT MAX(ts_utc) - INTERVAL {{ var('meter_lookback_days') }} DAY FROM {{ this }})
    {% endif %}
),

meters AS (
    SELECT meter_id, building_id, utility FROM {{ ref('stg_truth__meter') }}
),

joined AS (
    SELECT
        c.meter_id,
        c.ts_utc,
        c.value_kwh,
        m.utility,
        m.building_id
    FROM cleaned AS c
    -- Inner join: drop planted defect meters (M-*-*xx, ~297 rows, never in
    -- the register) so the fact conforms to dim_meter. Counts in ACCEPTANCE.
    INNER JOIN meters AS m USING (meter_id)
    WHERE CAST(c.ts_utc AS DATE) BETWEEN DATE '2026-01-01' AND DATE '2026-03-31'
)

SELECT * FROM joined
