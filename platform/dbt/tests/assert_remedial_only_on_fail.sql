SELECT inspection_id
FROM {{ ref('mart_compliance_status') }}
WHERE status = 'Failed - remedial open' AND result != 'Fail'
