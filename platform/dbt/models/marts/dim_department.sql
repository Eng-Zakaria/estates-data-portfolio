WITH source AS (
    SELECT
        department_id,
        department_name,
        faculty,
        staff_fte,
        student_fte
    FROM {{ ref('stg_truth__department') }}
)
SELECT * FROM source
