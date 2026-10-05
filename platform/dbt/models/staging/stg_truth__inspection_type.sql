WITH source AS (
    SELECT * FROM {{ source('truth', 'inspection_types') }}
),

renamed AS (
    SELECT
        inspection_type_id AS inspection_type_id,
        name AS inspection_name,
        frequency_months AS frequency_months,
        applies_to_asset_type AS applies_to_asset_type
    FROM source
)

SELECT * FROM renamed
