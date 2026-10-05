-- v04_summer_gas.sql — summer gas use per m2 by building (June–Aug, synthetic).
-- Empty on the small profile (window ends 2026-03-31): run on the default
-- profile to check the planted B019 summer-heating finding. Ties to: page 4.
SELECT
    d.building_id,
    ROUND(SUM(d.kwh), 1) AS summer_gas_kwh,
    ROUND(SUM(d.kwh) / NULLIF(MAX(b.gia_m2), 0), 3) AS summer_gas_kwh_per_m2
FROM main.fct_energy_daily AS d
JOIN main.dim_building AS b USING (building_id)
WHERE d.utility = 'gas'
  AND EXTRACT('month' FROM d.energy_date) IN (6, 7, 8)
GROUP BY 1
ORDER BY summer_gas_kwh_per_m2 DESC;
