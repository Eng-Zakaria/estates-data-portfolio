SELECT meter_id, energy_date, kwh
FROM {{ ref('fct_energy_daily') }}
WHERE kwh < 0
