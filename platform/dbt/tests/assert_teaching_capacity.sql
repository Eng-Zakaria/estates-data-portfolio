SELECT space_id
FROM {{ ref('dim_space') }}
WHERE space_category = 'Teaching' AND (capacity_seats IS NULL OR capacity_seats <= 0)
