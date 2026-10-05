-- v04_remedial_ageing.sql — Remedial actions ageing.
-- Ties to: Power BI page 4.
SELECT
    r.remedial_id,
    r.inspection_id,
    r.building_id,
    r.inspection_type_id,
    r.opened_date,
    r.closed_date,
    CASE
        WHEN r.closed_date IS NOT NULL
            THEN (r.closed_date - r.opened_date)
        ELSE (CURRENT_DATE - r.opened_date)
    END AS ageing_days,
    CASE
        WHEN r.closed_date IS NOT NULL THEN 'Closed'
        WHEN (CURRENT_DATE - r.opened_date) > 90 THEN 'Ageing >90d'
        WHEN (CURRENT_DATE - r.opened_date) > 30 THEN 'Ageing 31-90d'
        ELSE 'Ageing <=30d'
    END AS ageing_band,
    r.description,
    r.contractor,
    r.estimated_cost_gbp
FROM read_parquet('data/gold/remedial_actions.parquet') AS r
ORDER BY ageing_days DESC;