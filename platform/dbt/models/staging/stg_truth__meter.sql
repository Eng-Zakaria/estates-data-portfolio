WITH source AS (
    SELECT * FROM {{ source('truth', 'meters') }}
),
renamed AS (
    SELECT
        meter_id AS meter_id,
        building_id AS building_id,
        utility AS utility,
        meter_role AS meter_role,
        CAST(parent_meter_id AS VARCHAR) AS parent_meter_id,
        unit AS unit
    FROM source
)
SELECT * FROM renamed
