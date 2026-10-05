SELECT meter_id, ts_utc, COUNT(*) AS n
FROM {{ ref('fct_meter_hh') }}
GROUP BY 1, 2
HAVING COUNT(*) > 1
