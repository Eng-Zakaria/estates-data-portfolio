-- No fabricated rows: every fact row must exist in the cleaned input.
-- Dropped input rows (defect meters M-*-*xx, out-of-window dates 2099/2026-04-01)
-- are documented in docs/ACCEPTANCE_P04.md and intentionally excluded here.
SELECT f.meter_id, f.ts_utc
FROM {{ ref('fct_meter_hh') }} AS f
LEFT JOIN {{ ref('int_meter_hh_cleaned') }} AS i USING (meter_id, ts_utc)
WHERE i.meter_id IS NULL
