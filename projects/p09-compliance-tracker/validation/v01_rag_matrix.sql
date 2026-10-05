-- v01_rag_matrix.sql — Executive RAG matrix (inspection type × building).
-- Ties to: Power BI page 1.
WITH base AS (
    SELECT
        f.building_id,
        f.inspection_type_id,
        i.inspection_name,
        f.due_date,
        f.completed_date,
        f.result,
        r.opened_date AS remedial_opened,
        r.closed_date AS remedial_closed,
        CURRENT_DATE AS as_of  -- replaced at runtime by build script
    FROM main.fct_inspection AS f
    JOIN main.dim_inspection_type AS i USING (inspection_type_id)
    LEFT JOIN read_parquet('data/gold/remedial_actions.parquet') AS r
        ON r.inspection_id = f.inspection_id
),
status AS (
    SELECT
        *,
        CASE
            WHEN result = 'Fail' AND remedial_opened IS NOT NULL AND remedial_closed IS NULL
                THEN 'Failed – remedial open'
            WHEN due_date IS NULL AND completed_date IS NULL
                THEN 'No record'
            WHEN completed_date IS NOT NULL AND completed_date <= due_date
                THEN 'Compliant'
            WHEN completed_date IS NOT NULL AND completed_date > due_date
                THEN 'Overdue'
            WHEN due_date IS NOT NULL AND due_date <= as_of
                THEN 'Overdue'
            WHEN due_date IS NOT NULL AND due_date <= as_of + INTERVAL '30 days'
                THEN 'Due within 30 days'
            ELSE 'Compliant'
        END AS status,
        CASE
            WHEN due_date IS NOT NULL AND due_date <= as_of
                THEN (as_of - due_date)
            ELSE 0
        END AS days_overdue
    FROM base
),
rag AS (
    SELECT
        building_id,
        inspection_type_id,
        inspection_name,
        status,
        days_overdue,
        CASE
            WHEN status = 'Overdue' AND days_overdue > 90 THEN 'RED'
            WHEN status = 'Overdue' AND days_overdue > 30 THEN 'AMBER'
            WHEN status = 'Due within 30 days' THEN 'AMBER'
            WHEN status = 'Failed – remedial open' THEN 'RED'
            ELSE 'GREEN'
        END AS rag
    FROM status
)
SELECT * FROM rag ORDER BY building_id, inspection_type_id;