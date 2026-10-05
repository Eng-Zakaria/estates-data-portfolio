WITH inspections AS (
    SELECT * FROM {{ ref('fct_inspection') }}
),

status AS (
    SELECT
        inspection_id,
        building_id,
        inspection_type_id,
        due_date,
        completed_date,
        result,
        CASE
            WHEN result = 'Fail' THEN 'Failed - remedial open'
            WHEN completed_date IS NULL AND due_date < CURRENT_DATE THEN 'Overdue'
            WHEN completed_date IS NULL AND due_date <= CURRENT_DATE + INTERVAL 30 DAY THEN 'Due within 30 days'
            WHEN completed_date IS NOT NULL THEN 'Compliant'
            ELSE 'No record'
        END AS status,
        CASE WHEN completed_date IS NULL THEN DATE_DIFF('day', due_date, CURRENT_DATE) ELSE 0 END AS days_overdue
    FROM inspections
)

SELECT
    *,
    CASE status
        WHEN 'Failed - remedial open' THEN 4
        WHEN 'Overdue' THEN CASE WHEN days_overdue > 90 THEN 3 ELSE 2 END
        WHEN 'Due within 30 days' THEN 1
        ELSE 0
    END AS risk_score
FROM status
