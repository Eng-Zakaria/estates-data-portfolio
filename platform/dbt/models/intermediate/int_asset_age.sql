WITH assets AS (
    SELECT * FROM {{ ref('stg_truth__asset') }}
),

with_age AS (
    SELECT
        *,
        DATE_DIFF('year', CAST(install_date AS DATE), CURRENT_DATE) AS age_years
    FROM assets
),

aged AS (
    SELECT
        asset_id,
        building_id,
        space_id,
        asset_type,
        CAST(install_date AS DATE) AS install_date,
        expected_life_years,
        age_years,
        condition_grade,
        criticality,
        replacement_cost_gbp,
        {{ safe_divide('expected_life_years - age_years', 'expected_life_years') }} AS remaining_life_pct
    FROM with_age
)

SELECT * FROM aged
