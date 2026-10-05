WITH inspections AS (
    SELECT * FROM {{ ref('stg_insp__inspection') }}
),

types AS (
    SELECT inspection_type_id, frequency_months FROM {{ ref('stg_truth__inspection_type') }}
)

SELECT
    i.inspection_id,
    i.building_id,
    i.inspection_type_id,
    t.frequency_months,
    i.due_date,
    i.completed_date,
    i.result
FROM inspections AS i
LEFT JOIN types AS t USING (inspection_type_id)
