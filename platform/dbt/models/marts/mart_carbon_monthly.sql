WITH daily AS (
    SELECT * FROM {{ ref('fct_energy_daily') }}
),

factors AS (
    SELECT fuel, factor_kgco2e_per_kwh, factor_year FROM {{ ref('dim_emission_factor') }}
),

fuel_map AS (
    SELECT
        CAST(DATE_TRUNC('month', energy_date) AS DATE) AS month,
        CASE utility WHEN 'electricity' THEN 'electricity' WHEN 'gas' THEN 'natural_gas' ELSE NULL END AS fuel,
        SUM(kwh) AS kwh
    FROM daily
    WHERE utility IN ('electricity', 'gas')
    GROUP BY 1, 2
),

with_factors AS (
    SELECT
        m.month,
        m.fuel,
        m.kwh,
        f.factor_kgco2e_per_kwh,
        f.factor_year,
        {{ kwh_to_kgco2e('m.kwh', 'f.factor_kgco2e_per_kwh') }} AS kgco2e
    FROM fuel_map AS m
    LEFT JOIN factors AS f ON f.fuel = m.fuel
),

baseline AS (
    SELECT fuel, AVG(kwh) AS baseline_kwh
    FROM fuel_map
    WHERE EXTRACT('year' FROM month) = {{ var('carbon_base_year') }}
    GROUP BY 1
),

pathway AS (
    SELECT
        w.month,
        w.fuel,
        w.kwh,
        w.kgco2e,
        b.baseline_kwh,
        {{ safe_divide('w.kwh - b.baseline_kwh', 'b.baseline_kwh') }} AS variance_to_baseline
    FROM with_factors AS w
    LEFT JOIN baseline AS b USING (fuel)
)

SELECT * FROM pathway
