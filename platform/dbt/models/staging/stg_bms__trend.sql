WITH source AS (
    SELECT * FROM {{ source('silver', 'bms_trends') }}
),
renamed AS (
    SELECT
        point_id AS point_id,
        ts_utc AS ts_utc,
        value AS value
    FROM source
)
SELECT * FROM renamed
