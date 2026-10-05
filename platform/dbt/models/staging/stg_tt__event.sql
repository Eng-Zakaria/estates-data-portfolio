WITH source AS (
    SELECT * FROM {{ source('silver', 'timetable') }}
),
renamed AS (
    SELECT
        event_id AS event_id,
        space_id AS space_id,
        date AS event_date,
        t_start AS start_time,
        t_end AS end_time,
        module_code AS module_code,
        group_size AS group_size
    FROM source
)
SELECT * FROM renamed
