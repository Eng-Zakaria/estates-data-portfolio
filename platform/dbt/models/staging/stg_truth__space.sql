WITH source AS (
    SELECT * FROM {{ source('truth', 'spaces') }}
),
renamed AS (
    SELECT
        space_id AS space_id,
        room_code AS room_code,
        building_id AS building_id,
        space_category AS space_category,
        capacity_seats AS capacity_seats,
        nia_m2 AS nia_m2
    FROM source
)
SELECT * FROM renamed
