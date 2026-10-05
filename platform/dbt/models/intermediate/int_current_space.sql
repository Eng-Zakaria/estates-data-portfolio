WITH spaces AS (
    SELECT * FROM {{ ref('stg_space__register') }}
),

-- Canonical space master: silver carries room_code (B-...) while timetable,
-- CAFM and assets use space_id (S-...). Conform here so every downstream
-- grain matches. Silver is a subset of truth (5 planted-defect rooms were
-- quarantined in P01), so an inner join keeps all 495 conformed rooms.
mapping AS (
    SELECT space_id AS canonical_space_id, room_code FROM {{ ref('stg_truth__space') }}
),

buildings AS (
    SELECT * FROM {{ ref('stg_truth__building') }}
),

current_space AS (
    SELECT
        m.canonical_space_id AS space_id,
        s.room_code,
        s.building_id,
        s.space_category,
        s.nia_m2,
        s.capacity_seats,
        b.building_name,
        b.campus,
        b.gia_m2
    FROM spaces AS s
    INNER JOIN mapping AS m ON m.room_code = s.room_code
    LEFT JOIN buildings AS b USING (building_id)
)

SELECT * FROM current_space
