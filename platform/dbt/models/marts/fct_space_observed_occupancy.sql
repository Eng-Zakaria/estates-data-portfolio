WITH readings AS (
    SELECT * FROM {{ ref('stg_sensor__reading') }}
),

register AS (
    SELECT sensor_id, space_id
    FROM {{ ref('stg_truth__sensor') }}
    WHERE sensor_type = 'occupancy_count'
),

-- Inner join: drop readings from spaces quarantined in P01 (defect rooms;
-- counted in docs/ACCEPTANCE_P04.md) so the fact conforms to dim_space.
conformed AS (
    SELECT
        r.sensor_id,
        g.space_id,
        CAST(r.ts_utc AS TIMESTAMPTZ) AS ts_utc,
        CAST(r.value AS DOUBLE) AS observed_count
    FROM readings AS r
    INNER JOIN register AS g USING (sensor_id)
    INNER JOIN {{ ref('int_current_space') }} AS s USING (space_id)
)

SELECT * FROM conformed
