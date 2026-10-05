WITH readings AS (
    SELECT * FROM {{ ref('stg_sensor__reading') }}
),

register AS (
    SELECT sensor_id, space_id, sensor_type FROM {{ ref('stg_truth__sensor') }}
)

SELECT
    r.sensor_id,
    g.space_id,
    g.sensor_type,
    CAST(r.ts_utc AS TIMESTAMPTZ) AS ts_utc,
    CAST(r.value AS DOUBLE) AS value
FROM readings AS r
LEFT JOIN register AS g USING (sensor_id)
