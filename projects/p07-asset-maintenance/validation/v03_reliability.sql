-- v03_reliability.sql -- bad actors: top-10 assets by reactive jobs (12m window).
-- MTBF assets with >= 2 reactive completions. Trade Pareto (fault-code proxy).
-- Ties to: Power BI page 3.
SELECT
    h.asset_id, h.building_id, h.asset_type, h.condition_grade,
    h.reactive_12m, h.is_repeat_failure, h.risk_score
FROM main.mart_asset_health AS h
ORDER BY h.reactive_12m DESC, h.risk_score DESC
LIMIT 10;

WITH events AS (
    SELECT asset_id,
           CAST(completed_ts AS TIMESTAMP) AS completed_ts,
           ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY completed_ts) AS rn,
           COUNT(*) OVER (PARTITION BY asset_id) AS n
    FROM main.fct_work_order
    WHERE wo_type = 'Reactive' AND status = 'Complete'
),
gaps AS (
    SELECT asset_id,
           DATE_DIFF('day', LAG(completed_ts) OVER (PARTITION BY asset_id ORDER BY completed_ts), completed_ts) AS gap_days,
           n
    FROM events
)
SELECT asset_id, n, ROUND(AVG(gap_days), 1) AS mtbf_days
FROM gaps
WHERE n >= 2 AND gap_days IS NOT NULL
GROUP BY 1, 2
ORDER BY n DESC, mtbf_days ASC
LIMIT 10;

SELECT trade, COUNT(*) FILTER (WHERE wo_type = 'Reactive') AS reactive,
       ROUND(SUM(cost_gbp) FILTER (WHERE wo_type = 'Reactive'), 0) AS reactive_cost
FROM main.fct_work_order
GROUP BY 1 ORDER BY 2 DESC;
