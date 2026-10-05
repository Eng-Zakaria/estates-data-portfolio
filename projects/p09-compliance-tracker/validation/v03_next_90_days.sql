-- v03_next_90_days.sql — Next 90 days calendar and workload by week/contractor.
-- Ties to: Power BI page 3.
WITH upcoming AS (
    SELECT
        f.inspection_id,
        f.building_id,
        f.inspection_type_id,
        f.due_date,
        i.inspection_name,
        r.contractor AS remedial_contractor
    FROM main.fct_inspection AS f
    JOIN main.dim_inspection_type AS i USING (inspection_type_id)
    LEFT JOIN read_parquet('data/gold/remedial_actions.parquet') AS r
        ON r.inspection_id = f.inspection_id
    WHERE f.due_date IS NOT NULL
      AND f.due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '90 days'
)
SELECT
    due_date,
    EXTRACT('week' FROM due_date) AS week_num,
    COUNT(*) AS inspections_due,
    COUNT(DISTINCT building_id) AS buildings_affected,
    STRING_AGG(DISTINCT inspection_name, ', ') AS types_due
FROM upcoming
GROUP BY due_date, week_num
ORDER BY due_date;