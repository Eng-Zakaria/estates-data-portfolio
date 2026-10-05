-- v01_scope_totals.sql — headline KPI: kWh and kgCO2e by scope (synthetic).
-- Ties to: Power BI page 1 KPI cards. Run from the repo root.
WITH daily AS (
    SELECT * FROM main.fct_energy_daily
),
factors AS (
    SELECT fuel, scope, factor_kgco2e_per_kwh FROM main.dim_emission_factor
)
SELECT
    f.scope,
    SUM(d.kwh) AS kwh,
    SUM(d.kwh * f.factor_kgco2e_per_kwh) AS kgco2e
FROM daily AS d
JOIN factors AS f
    ON f.fuel = CASE d.utility WHEN 'electricity' THEN 'electricity'
                                WHEN 'gas' THEN 'natural_gas' END
GROUP BY 1
ORDER BY 1;
