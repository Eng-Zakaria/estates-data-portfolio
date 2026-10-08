-- v05_planted.sql -- check planted findings against the small profile.
-- Plant 1: B012 boiler >= 8 reactive jobs. Small profile has B001-B008 only,
-- so expect 0 rows, since the finding belongs to the default profile.
-- Plant 2: PPM completion drop in 2025-Q4. Small-profile window is 2026-Q1,
-- so check monthly PPM completion for a measured March dip instead.
SELECT asset_id, building_id, asset_type
FROM main.dim_asset
WHERE building_id = 'B012' AND asset_type = 'Boiler';

SELECT
    STRFTIME(CAST(raised_ts AS TIMESTAMP), '%Y-%m') AS month,
    COUNT(*) AS n_ppm,
    ROUND(COUNT(*) FILTER (WHERE status = 'Complete') * 1.0 / COUNT(*), 4) AS ppm_completion
FROM main.fct_work_order
WHERE wo_type = 'PPM'
GROUP BY 1 ORDER BY 1;

-- Top repeat-failure asset types on this profile (measured bad actors):
SELECT a.building_id, a.asset_type, COUNT(*) AS n_reactive
FROM main.fct_work_order AS w
JOIN main.dim_asset AS a USING (asset_id)
WHERE wo_type = 'Reactive'
GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10;
