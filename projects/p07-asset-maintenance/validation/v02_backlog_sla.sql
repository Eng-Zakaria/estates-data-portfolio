-- v02_backlog_sla.sql -- backlog count + age bands (as-of 2026-03-31), SLA met % by priority.
-- SLA targets are illustrative config (methodology.md): P1 1d, P2 5d, P3 10d, P4 20d.
-- Ties to: Power BI page 2.
WITH params AS (SELECT DATE '2026-03-31' AS as_of),
aged AS (
    SELECT w.*, DATE_DIFF('day', CAST(w.raised_ts AS TIMESTAMP), params.as_of) AS age_days
    FROM main.fct_work_order AS w, params
    WHERE w.is_open
)
SELECT
    CASE
        WHEN age_days <= 30 THEN '0-30'
        WHEN age_days <= 90 THEN '31-90'
        WHEN age_days <= 180 THEN '91-180'
        ELSE '180+'
    END AS age_band,
    count(*) AS n_backlog,
    ROUND(AVG(age_days), 1) AS avg_age_days
FROM aged
GROUP BY 1
ORDER BY 1;

SELECT
    priority,
    count(*) FILTER (WHERE status = 'Complete') AS n_complete,
    ROUND(AVG(CASE WHEN days_to_complete <=
                   CASE priority WHEN 'P1' THEN 1 WHEN 'P2' THEN 5
                                WHEN 'P3' THEN 10 WHEN 'P4' THEN 20 END
              THEN 1.0 ELSE 0.0 END)
          FILTER (WHERE status = 'Complete'), 4) AS sla_met_pct
FROM main.fct_work_order
GROUP BY 1 ORDER BY 1;
