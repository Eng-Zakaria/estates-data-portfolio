{% snapshot snap_assets %}

{{
    config(
        target_schema='snapshots',
        strategy='check',
        unique_key='asset_id',
        check_cols='all'
    )
}}

SELECT
    asset_id,
    building_id,
    space_id,
    asset_type,
    install_date,
    expected_life_years,
    condition_grade,
    criticality,
    replacement_cost_gbp
FROM {{ ref('stg_truth__asset') }}

{% endsnapshot %}
