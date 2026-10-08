-- v04_lifecycle.sql -- condition profile, remaining life, 5-yr renewal forecast, cost per m2.
-- Ties to: Power BI page 4.
SELECT condition_grade, COUNT(*) AS n_assets,
       ROUND(SUM(replacement_cost_gbp), 0) AS replacement_value
FROM main.mart_asset_health
GROUP BY 1 ORDER BY 1;

SELECT
    CASE
        WHEN remaining_life_pct IS NULL THEN 'unknown'
        WHEN remaining_life_pct < 0 THEN 'over-life'
        WHEN remaining_life_pct < 0.25 THEN '0-25%'
        WHEN remaining_life_pct < 0.5 THEN '25-50%'
        WHEN remaining_life_pct < 0.75 THEN '50-75%'
        ELSE '75-100%'
    END AS life_band,
    COUNT(*) AS n_assets
FROM main.mart_asset_health
GROUP BY 1 ORDER BY 1;

-- 5-year renewal forecast: install_date.year + expected_life_years.
SELECT
    year(a.install_date) + a.expected_life_years AS renewal_year,
    COUNT(*) AS n_assets,
    ROUND(SUM(a.replacement_cost_gbp), 0) AS forecast_cost_gbp
FROM main.dim_asset AS a
WHERE a.install_date IS NOT NULL AND a.expected_life_years IS NOT NULL
GROUP BY 1
HAVING renewal_year BETWEEN 2026 AND 2030
ORDER BY 1;

SELECT
    ROUND(SUM(w.cost_gbp) FILTER (WHERE w.cost_gbp IS NOT NULL), 0) /
        NULLIF(SUM(b.gia_m2), 0) AS cost_per_gia_m2_gbp
FROM main.fct_work_order AS w
JOIN main.dim_building AS b USING (building_id);
