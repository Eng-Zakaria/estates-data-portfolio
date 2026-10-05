WITH assets AS (
    SELECT * FROM {{ ref('int_asset_age') }}
),

reactive AS (
    SELECT
        asset_id,
        COUNT(*) AS reactive_12m
    FROM {{ ref('fct_work_order') }}
    WHERE wo_type = 'Reactive'
    GROUP BY 1
)

SELECT
    a.asset_id,
    a.building_id,
    a.asset_type,
    a.condition_grade,
    a.criticality,
    a.age_years,
    a.remaining_life_pct,
    a.replacement_cost_gbp,
    COALESCE(r.reactive_12m, 0) AS reactive_12m,
    CASE WHEN COALESCE(r.reactive_12m, 0) >= 3 THEN TRUE ELSE FALSE END AS is_repeat_failure,
    a.criticality * CASE a.condition_grade WHEN 'A' THEN 1 WHEN 'B' THEN 2 WHEN 'C' THEN 3 ELSE 4 END AS risk_score
FROM assets AS a
LEFT JOIN reactive AS r USING (asset_id)
