SELECT asset_id, age_years, remaining_life_pct
FROM {{ ref('mart_asset_health') }}
-- Negative remaining_life_pct is a valid business state (asset beyond
-- expected life = replacement backlog), not a data error. Flag only
-- impossible values: future install (negative age) or >100% remaining.
WHERE age_years < 0 OR remaining_life_pct > 1.0001
