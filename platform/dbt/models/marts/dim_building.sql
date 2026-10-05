WITH source AS (
    SELECT
        building_id,
        building_name,
        campus,
        gia_m2,
        nia_m2,
        n_floors,
        year_built,
        primary_use,
        heating_fuel,
        epc_band
    FROM {{ ref('stg_truth__building') }}
)
SELECT * FROM source
