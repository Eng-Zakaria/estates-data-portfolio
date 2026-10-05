WITH source AS (
    SELECT * FROM {{ source('silver', 'cafm_workorders') }}
),
renamed AS (
    SELECT
        "WO_Number" AS wo_id,
        "AssetRef" AS asset_id,
        space_id AS space_id,
        building_id AS building_id,
        wo_type AS wo_type,
        priority AS priority,
        raised_ts AS raised_ts,
        completed_ts AS completed_ts,
        status AS status,
        trade AS trade,
        contractor AS contractor,
        labour_hours AS labour_hours,
        cost_gbp AS cost_gbp
    FROM source
)
SELECT * FROM renamed
