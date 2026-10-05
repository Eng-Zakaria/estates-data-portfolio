WITH source AS (
    SELECT * FROM {{ source('truth', 'buildings') }}
),
renamed AS (
    SELECT
        building_id AS building_id,
        building_name AS building_name,
        campus AS campus,
        gia_m2 AS gia_m2,
        nia_m2 AS nia_m2,
        n_floors AS n_floors,
        year_built AS year_built,
        primary_use AS primary_use,
        heating_fuel AS heating_fuel,
        epc_band AS epc_band
    FROM source
)
SELECT * FROM renamed
