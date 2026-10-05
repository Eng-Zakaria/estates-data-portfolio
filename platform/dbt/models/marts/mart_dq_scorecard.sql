WITH snapshot AS (
    SELECT * FROM {{ ref('seed_dq_snapshot') }}
)

SELECT
    dataset,
    grain,
    CAST(rows_checked AS INTEGER) AS rows_checked,
    CAST(rows_quarantined AS INTEGER) AS rows_quarantined,
    CAST(pass_rate AS DOUBLE) AS pass_rate
FROM snapshot
