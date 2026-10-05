WITH source AS (
    SELECT * FROM {{ source('truth', 'sensors') }}
),

renamed AS (
    SELECT
        sensor_id AS sensor_id,
        space_id AS space_id,
        sensor_type AS sensor_type,
        CAST(install_date AS DATE) AS install_date
    FROM source
)

SELECT * FROM renamed
