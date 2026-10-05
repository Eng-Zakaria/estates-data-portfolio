SELECT wo_id, raised_ts, completed_ts
FROM {{ ref('fct_work_order') }}
WHERE completed_ts IS NOT NULL AND completed_ts < raised_ts
