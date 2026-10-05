WITH factors AS (
    SELECT * FROM {{ ref('seed_emission_factors') }}
)

SELECT
    fuel,
    scope,
    unit,
    CAST(factor_kgco2e_per_kwh AS DOUBLE) AS factor_kgco2e_per_kwh,
    CAST(year AS INTEGER) AS factor_year,
    source_url
FROM factors
