WITH source AS (
    SELECT
        space_id,
        room_code,
        building_id,
        space_category,
        nia_m2,
        capacity_seats,
        building_name,
        campus,
        gia_m2
    FROM {{ ref('int_current_space') }}
)
SELECT * FROM source
