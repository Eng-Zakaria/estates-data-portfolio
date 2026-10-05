WITH calendar AS (
    SELECT * FROM {{ ref('seed_academic_calendar') }}
),

dated AS (
    SELECT
        CAST(date AS DATE) AS date_day,
        CAST(date AS DATE) AS full_date,
        EXTRACT('year' FROM CAST(date AS DATE)) AS year,
        EXTRACT('month' FROM CAST(date AS DATE)) AS month,
        EXTRACT('isodow' FROM CAST(date AS DATE)) AS day_of_week,
        term,
        teaching_week,
        is_holiday,
        is_weekend
    FROM calendar
)

SELECT * FROM dated
