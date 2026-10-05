{% snapshot snap_spaces %}

{{
    config(
        target_schema='snapshots',
        strategy='check',
        unique_key='room_code',
        check_cols='all'
    )
}}

SELECT
    room_code,
    building_id,
    building_name,
    space_category,
    nia_m2,
    capacity_seats
FROM {{ ref('stg_space__register') }}

{% endsnapshot %}
