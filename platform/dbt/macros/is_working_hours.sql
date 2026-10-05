{% macro is_working_hours(ts_col) %}
    (
        EXTRACT('isodow' FROM {{ uk_local_ts(ts_col) }}) BETWEEN 1 AND 5
        AND EXTRACT('hour' FROM {{ uk_local_ts(ts_col) }}) >= 9
        AND EXTRACT('hour' FROM {{ uk_local_ts(ts_col) }}) < 18
    )
{% endmacro %}
