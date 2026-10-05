-- v02_rooms_to_review.sql — low-utilisation, high-no-show, mismatch rooms (synthetic).
-- No-show = booked event with sensor coverage whose max valid observed count
-- is < 1. Invalid (negative) readings excluded. Ties to: page 3 table.
WITH events AS (
    SELECT
        e.event_id, e.space_id, e.event_date, e.start_time, e.end_time,
        e.group_size, s.capacity_seats
    FROM main.fct_timetable_event AS e
    JOIN main.dim_space AS s USING (space_id)
),
event_occ AS (
    SELECT
        e.event_id,
        e.space_id,
        e.group_size,
        e.capacity_seats,
        COUNT(o.ts_utc) AS n_readings,
        MAX(o.observed_count) AS max_observed
    FROM events AS e
    LEFT JOIN main.fct_space_observed_occupancy AS o
      ON o.space_id = e.space_id
     AND CAST(o.ts_utc AT TIME ZONE 'Europe/London' AS DATE) = e.event_date
     AND CAST(o.ts_utc AT TIME ZONE 'Europe/London' AS TIME)
         BETWEEN CAST(e.start_time AS TIME) AND CAST(e.end_time AS TIME)
     AND o.observed_count >= 0
    GROUP BY 1, 2, 3, 4
),
per_space AS (
    SELECT
        space_id,
        SUM(CASE WHEN n_readings > 0 AND max_observed < 1.0 THEN 1 ELSE 0 END) AS no_shows,
        SUM(CASE WHEN n_readings = 0 THEN 1 ELSE 0 END) AS events_no_coverage,
        SUM(CASE WHEN group_size < 0.5 * capacity_seats THEN 1 ELSE 0 END) AS mismatch_events
    FROM event_occ
    GROUP BY 1
)
SELECT
    m.space_id, m.building_id, m.space_category, m.capacity_seats,
    m.n_events, ROUND(m.booked_hours, 1) AS booked_hours,
    ROUND(m.frequency_rate, 3) AS frequency_rate,
    ROUND(m.occupancy_rate, 3) AS occupancy_rate,
    ROUND(m.frequency_rate * m.occupancy_rate, 3) AS utilisation,
    COALESCE(p.no_shows, 0) AS no_shows,
    COALESCE(p.events_no_coverage, 0) AS events_no_coverage,
    COALESCE(p.mismatch_events, 0) AS mismatch_events
FROM main.mart_space_utilisation AS m
LEFT JOIN per_space AS p USING (space_id)
ORDER BY utilisation ASC NULLS LAST;
