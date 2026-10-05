-- v01_overview.sql — headline KPIs: frequency, occupancy, utilisation (synthetic).
-- Frequency uses mart booked hours over dim_date teaching availability.
-- Ties to: Power BI page 1 KPI cards.
WITH avail AS (
    SELECT COUNT(*) * 9.0 AS available_hours
    FROM main.dim_date
    WHERE teaching_week > 0 AND NOT is_weekend AND NOT is_holiday
)
SELECT
    COUNT(*) AS n_spaces,
    ROUND(SUM(booked_hours), 1) AS timetabled_hours,
    (SELECT available_hours FROM avail) AS available_hours_per_space,
    ROUND(SUM(booked_hours) / NULLIF(COUNT(*) * (SELECT available_hours FROM avail), 0), 4) AS frequency_rate,
    ROUND(AVG(occupancy_rate), 4) AS avg_occupancy_rate,
    ROUND(AVG(frequency_rate * occupancy_rate), 4) AS avg_utilisation
FROM main.mart_space_utilisation;
