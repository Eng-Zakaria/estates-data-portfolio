WITH source AS (
    SELECT * FROM {{ source('silver', 'meter_hh_supplierA') }}
),
renamed AS (
    SELECT
        meter_id AS meter_id,
        ts_utc AS ts_utc,
        value AS value_kwh,
        unit AS unit,
        quality_flag AS quality_flag
    FROM source
)
SELECT * FROM renamed
