-- v05_trend.sql — Monthly compliance trend (synthetic 12 months from date-shift).
-- Ties to: Power BI page 5.
WITH months AS (
    SELECT
        DATE_TRUNC('month', d)::DATE AS month,
        f.building_id,
        f.inspection_type_id,
        f.due_date,
        f.completed_date,
        f.result,
        r.opened_date AS remedial_opened,
        r.closed_date AS remedial_closed
    FROM main.fct_inspection AS f
    LEFT JOIN read_parquet('data/gold/remedial_actions.parquet') AS r
        ON r.inspection_id = f.inspection_id
    CROSS JOIN LATERAL (
        SELECT generate_series(
            DATE '2025-04-01',
            DATE '2026-03-01',
            INTERVAL '1 month'
        ) AS d
    ) AS d
)
SELECT
    month,
    COUNT(*) AS total_inspections,
    COUNT(*) FILTER (WHERE due_date <= month AND (completed_date IS NULL OR completed_date > due_date)) AS overdue,
    COUNT(*) FILTER (WHERE result = 'Fail' AND remedial_opened IS NOT NULL AND (remedial_closed IS NULL OR remedial_closed > month)) AS failed_remedial_open,
    COUNT(*) FILTER (WHERE completed_date IS NOT NULL AND completed_date <= due_date AND due_date <= month) AS compliant
FROM months
GROUP BY month
ORDER BY month;