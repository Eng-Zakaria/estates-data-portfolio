WITH spaces AS (
    SELECT space_id, building_id, nia_m2 FROM {{ ref('dim_space') }}
),

totals AS (
    SELECT building_id, SUM(nia_m2) AS total_nia FROM spaces GROUP BY 1
),

gia AS (
    SELECT building_id, gia_m2 FROM {{ ref('dim_building') }}
)

SELECT t.building_id, t.total_nia, g.gia_m2
FROM totals AS t
JOIN gia AS g USING (building_id)
WHERE t.total_nia > g.gia_m2 * 1.0001
