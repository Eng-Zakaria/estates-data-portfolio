-- v05_b003_check.sql — planted-finding check: B003 teaching rooms with
-- frequency >= 70% but occupancy < 30% (synthetic). Ties to: pages 1-2.
SELECT
    space_id, n_events,
    ROUND(booked_hours, 1) AS booked_hours,
    ROUND(frequency_rate, 3) AS frequency_rate,
    ROUND(occupancy_rate, 3) AS occupancy_rate
FROM main.mart_space_utilisation
WHERE building_id = 'B003' AND space_category = 'Teaching'
  AND frequency_rate >= 0.70 AND occupancy_rate < 0.30
ORDER BY frequency_rate DESC;
