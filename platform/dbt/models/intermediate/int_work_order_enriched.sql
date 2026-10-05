WITH work_orders AS (
    SELECT * FROM {{ ref('stg_cafm__work_order') }}
),

enriched AS (
    SELECT
        wo_id,
        asset_id,
        space_id,
        building_id,
        wo_type,
        priority,
        CAST(raised_ts AS TIMESTAMPTZ) AS raised_ts,
        CAST(completed_ts AS TIMESTAMPTZ) AS completed_ts,
        status,
        trade,
        contractor,
        CAST(labour_hours AS DOUBLE) AS labour_hours,
        CAST(cost_gbp AS DOUBLE) AS cost_gbp,
        DATE_DIFF('day', CAST(raised_ts AS TIMESTAMPTZ), CAST(completed_ts AS TIMESTAMPTZ)) AS days_to_complete,
        CASE WHEN completed_ts IS NULL THEN TRUE ELSE FALSE END AS is_open,
        CASE
            WHEN wo_type = 'Reactive' THEN 'unplanned'
            WHEN wo_type = 'PPM' THEN 'planned'
            ELSE 'other_planned'
        END AS plan_category
    FROM work_orders
)

SELECT * FROM enriched
