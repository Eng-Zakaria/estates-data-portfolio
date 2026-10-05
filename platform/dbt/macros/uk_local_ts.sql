{% macro uk_local_ts(ts_col) %}
    (TIMEZONE('Europe/London', CAST({{ ts_col }} AS TIMESTAMPTZ)))
{% endmacro %}
