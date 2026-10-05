WITH source AS (
    SELECT * FROM {{ source('truth', 'weather') }}
),

renamed AS (
    SELECT
        CAST(ts_utc AS TIMESTAMPTZ) AS ts_utc,
        CAST(temp_c AS DOUBLE) AS temp_c,
        CAST(hdd_base15_5 AS DOUBLE) AS hdd_base15_5,
        CAST(cdd AS DOUBLE) AS cdd
    FROM source
)

SELECT * FROM renamed
