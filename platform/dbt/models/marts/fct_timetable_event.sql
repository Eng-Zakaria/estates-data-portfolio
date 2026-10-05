WITH events AS (
    SELECT * FROM {{ ref('stg_tt__event') }}
),

durations AS (
    SELECT
        event_id,
        -- Grain conforms via int_current_space (canonical S- ids mapped from
        -- silver room_code); no re-keying here.
        space_id,
        CAST(event_date AS DATE) AS event_date,
        start_time,
        end_time,
        module_code,
        CAST(group_size AS INTEGER) AS group_size,
        (
            EXTRACT('hour' FROM CAST(end_time AS TIME)) * 60 + EXTRACT('minute' FROM CAST(end_time AS TIME))
            - EXTRACT('hour' FROM CAST(start_time AS TIME)) * 60 - EXTRACT('minute' FROM CAST(start_time AS TIME))
        ) / 60.0 AS duration_hours
    FROM events
    WHERE CAST(event_date AS DATE) BETWEEN DATE '2026-01-01' AND DATE '2026-03-31'
),

-- Inner join: drop rows whose space was quarantined in P01 (unmapped
-- category / out-of-range area defects, ~286 rows) so the fact conforms
-- to dim_space. Dropped counts are recorded in docs/ACCEPTANCE_P04.md.
conformed AS (
    SELECT d.*
    FROM durations AS d
    INNER JOIN {{ ref('int_current_space') }} AS s USING (space_id)
)

SELECT * FROM conformed
