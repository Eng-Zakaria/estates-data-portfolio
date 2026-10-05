{% macro kwh_to_kgco2e(kwh_col, factor_col) %}
    (CAST({{ kwh_col }} AS DOUBLE) * CAST({{ factor_col }} AS DOUBLE))
{% endmacro %}
