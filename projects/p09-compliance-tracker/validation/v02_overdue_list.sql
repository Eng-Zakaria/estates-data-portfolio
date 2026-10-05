-- v02_overdue_list.sql — Overdue list with drill-through context.
-- Ties to: Power BI page 2.
SELECT
    f.inspection_id,
    f.building_id,
    b.building_name,
    i.inspection_name,
    f.due_date,
    f.result,
    (CURRENT_DATE - f.due_date) AS days_overdue,
    CASE
        WHEN f.due_date IS NOT NULL AND f.due_date <= CURRENT_DATE
            THEN (CURRENT_DATE - f.due_date)
        ELSE 0
    END AS days_overdue_calc,
    r.opened_date AS remedial_opened,
    r.closed_date AS remedial_closed,
    r.description AS remedial_description,
    r.contractor AS remedial_contractor
FROM main.fct_inspection AS f
JOIN main.dim_building AS b USING (building_id)
JOIN main.dim_inspection_type AS i USING (inspection_type_id)
LEFT JOIN read_parquet('data/gold/remedial_actions.parquet') AS r
    ON r.inspection_id = f.inspection_id
WHERE f.due_date IS NOT NULL
  AND f.due_date <= CURRENT_DATE
  AND (f.completed_date IS NULL OR f.completed_date > f.due_date)
ORDER BY days_overdue_calc DESC;