-- v01_overview.sql -- headline: WO volumes, PPM completion, planned:reactive, MTTR, cost.
-- Ties to: Power BI page 1 KPI cards. Run from the repo root.
SELECT
    wo_type,
    count(*) AS n_total,
    count(*) FILTER (WHERE status = 'Complete') AS n_complete,
    count(*) FILTER (WHERE is_open) AS n_open,
    ROUND(SUM(cost_gbp), 0) AS total_cost_gbp
FROM main.fct_work_order
GROUP BY 1
ORDER BY 1;

SELECT
    ROUND(SUM(CASE WHEN wo_type = 'PPM' AND status = 'Complete' THEN 1 ELSE 0 END) * 1.0
          / NULLIF(SUM(CASE WHEN wo_type = 'PPM' THEN 1 ELSE 0 END), 0), 4) AS ppm_completion,
    ROUND(SUM(CASE WHEN plan_category IN ('planned', 'other_planned') THEN 1 ELSE 0 END) * 1.0
          / NULLIF(SUM(CASE WHEN plan_category = 'unplanned' THEN 1 ELSE 0 END), 0), 2) AS planned_reactive_ratio,
    ROUND(AVG(days_to_complete) FILTER (WHERE wo_type = 'Reactive' AND status = 'Complete'), 2) AS mttr_reactive_days,
    ROUND(SUM(cost_gbp), 0) AS total_cost_gbp
FROM main.fct_work_order;

SELECT trade, ROUND(SUM(cost_gbp), 0) AS cost_gbp
FROM main.fct_work_order
GROUP BY 1 ORDER BY 2 DESC;
