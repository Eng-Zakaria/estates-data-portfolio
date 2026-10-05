WITH trades AS (
    SELECT DISTINCT trade
    FROM {{ ref('int_work_order_enriched') }}
    WHERE trade IS NOT NULL
)

SELECT
    LOWER(REPLACE(trade, ' ', '_')) AS trade_id,
    trade AS trade
FROM trades
