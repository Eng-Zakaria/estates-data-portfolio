WITH source AS (
    SELECT * FROM {{ source('silver', 'space_register') }}
),
renamed AS (
    SELECT
        room_code AS room_code,
        building_id AS building_id,
        building_name AS building_name,
        space_category AS space_category,
        nia_m2 AS nia_m2,
        capacity_seats AS capacity_seats
    FROM source
)
SELECT * FROM renamed
