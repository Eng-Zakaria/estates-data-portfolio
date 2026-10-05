WITH enriched AS (
    SELECT
        wo_id,
        asset_id,
        space_id,
        building_id,
        wo_type,
        priority,
        raised_ts,
        completed_ts,
        status,
        trade,
        contractor,
        labour_hours,
        cost_gbp,
        days_to_complete,
        is_open,
        plan_category
    FROM {{ ref('int_work_order_enriched') }}
)

SELECT * FROM enriched
