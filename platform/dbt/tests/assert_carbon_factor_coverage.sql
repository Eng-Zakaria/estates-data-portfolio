SELECT month, fuel, kwh
FROM {{ ref('mart_carbon_monthly') }}
WHERE kwh > 0 AND kgco2e IS NULL
