WITH source AS (
    SELECT * FROM {{ source('truth', 'assets') }}
),
renamed AS (
    SELECT
        asset_id AS asset_id,
        building_id AS building_id,
        space_id AS space_id,
        asset_type AS asset_type,
        install_date AS install_date,
        expected_life_years AS expected_life_years,
        condition_grade AS condition_grade,
        criticality AS criticality,
        replacement_cost_gbp AS replacement_cost_gbp
    FROM source
)
SELECT * FROM renamed
