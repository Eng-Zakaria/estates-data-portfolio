WITH source AS (
    SELECT
        meter_id,
        building_id,
        utility,
        meter_role,
        parent_meter_id,
        unit
    FROM {{ ref('stg_truth__meter') }}
)
SELECT * FROM source
