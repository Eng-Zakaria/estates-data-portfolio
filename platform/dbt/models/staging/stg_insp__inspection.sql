WITH source AS (
    SELECT * FROM {{ source('silver', 'statutory_inspections') }}
),
renamed AS (
    SELECT
        inspection_id AS inspection_id,
        building_id AS building_id,
        inspection_type_id AS inspection_type_id,
        due_date AS due_date,
        completed_date AS completed_date,
        result AS result
    FROM source
)
SELECT * FROM renamed
