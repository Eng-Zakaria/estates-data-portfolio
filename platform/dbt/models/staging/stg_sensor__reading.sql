WITH source AS (
    SELECT * FROM {{ source('silver', 'sensors') }}
),
renamed AS (
    SELECT
        sensor_id AS sensor_id,
        ts_utc AS ts_utc,
        value AS value
    FROM source
)
SELECT * FROM renamed
