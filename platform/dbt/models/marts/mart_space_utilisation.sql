WITH events AS (
    SELECT * FROM {{ ref('fct_timetable_event') }}
),

spaces AS (
    SELECT space_id, building_id, space_category, nia_m2, capacity_seats FROM {{ ref('dim_space') }}
),

per_space AS (
    SELECT
        e.space_id,
        COUNT(*) AS n_events,
        SUM(e.duration_hours) AS booked_hours,
        AVG(e.group_size) AS avg_group_size
    FROM events AS e
    GROUP BY 1
),

available AS (
    SELECT CAST(COUNT(*) * 9.0 AS DOUBLE) AS available_hours
    FROM {{ ref('dim_date') }}
    WHERE teaching_week > 0 AND NOT is_weekend AND NOT is_holiday
)

SELECT
    s.space_id,
    s.building_id,
    s.space_category,
    s.nia_m2,
    s.capacity_seats,
    COALESCE(p.n_events, 0) AS n_events,
    COALESCE(p.booked_hours, 0.0) AS booked_hours,
    (SELECT available_hours FROM available) AS available_hours,
    {{ safe_divide('COALESCE(p.booked_hours, 0.0)', '(SELECT available_hours FROM available)') }} AS frequency_rate,
    {{ safe_divide('COALESCE(p.avg_group_size, 0.0)', 'NULLIF(s.capacity_seats, 0)') }} AS occupancy_rate,
    COALESCE(p.avg_group_size, 0.0) AS avg_group_size
FROM spaces AS s
LEFT JOIN per_space AS p USING (space_id)
