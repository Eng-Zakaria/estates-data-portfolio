-- v02_intensity.sql — kgCO2e/m2 (GIA) league table by building (synthetic).
-- Ties to: Power BI page 2 building league table.
WITH daily AS (
    SELECT building_id, utility, SUM(kwh) AS kwh
    FROM main.fct_energy_daily
    GROUP BY 1, 2
),
factors AS (
    SELECT fuel, factor_kgco2e_per_kwh FROM main.dim_emission_factor
),
carbon AS (
    SELECT
        d.building_id,
        SUM(d.kwh * f.factor_kgco2e_per_kwh) AS kgco2e,
        SUM(d.kwh) AS kwh
    FROM daily AS d
    JOIN factors AS f
        ON f.fuel = CASE d.utility WHEN 'electricity' THEN 'electricity'
                                    WHEN 'gas' THEN 'natural_gas' END
    GROUP BY 1
)
SELECT
    c.building_id,
    b.gia_m2,
    ROUND(c.kwh, 1) AS kwh,
    ROUND(c.kgco2e, 1) AS kgco2e,
    ROUND(c.kwh / NULLIF(b.gia_m2, 0), 3) AS kwh_per_m2,
    ROUND(c.kgco2e / NULLIF(b.gia_m2, 0), 4) AS kgco2e_per_m2
FROM carbon AS c
JOIN main.dim_building AS b USING (building_id)
ORDER BY kgco2e_per_m2 DESC;
