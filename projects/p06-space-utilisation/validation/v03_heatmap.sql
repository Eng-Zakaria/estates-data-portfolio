-- v03_heatmap.sql — day x hour utilisation matrix source (synthetic).
-- Cell = events in progress / rooms in scope. Ties to: page 2 heatmap.
WITH hours AS (
    SELECT
        CASE WHEN EXTRACT('isodow' FROM event_date) < 6 THEN 'weekday' ELSE 'weekend' END AS day_type,
        EXTRACT('hour' FROM CAST(start_time AS TIME)) AS start_hour,
        duration_hours
    FROM main.fct_timetable_event
)
SELECT
    day_type,
    start_hour,
    COUNT(*) AS n_event_starts,
    ROUND(SUM(duration_hours), 1) AS booked_hours
FROM hours
GROUP BY 1, 2
ORDER BY 1, 2;
