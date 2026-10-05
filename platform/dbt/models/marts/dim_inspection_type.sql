WITH source AS (
    SELECT
        inspection_type_id,
        inspection_name,
        frequency_months,
        applies_to_asset_type
    FROM {{ ref('stg_truth__inspection_type') }}
)
SELECT * FROM source
