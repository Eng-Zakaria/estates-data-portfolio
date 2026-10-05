SELECT event_id, duration_hours
FROM {{ ref('fct_timetable_event') }}
WHERE duration_hours IS NULL OR duration_hours <= 0
