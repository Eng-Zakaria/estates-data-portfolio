WITH source AS (
    SELECT * FROM {{ source('truth', 'departments') }}
),
renamed AS (
    SELECT
        department_id AS department_id,
        name AS department_name,
        faculty AS faculty,
        staff_fte AS staff_fte,
        student_fte AS student_fte
    FROM source
)
SELECT * FROM renamed
