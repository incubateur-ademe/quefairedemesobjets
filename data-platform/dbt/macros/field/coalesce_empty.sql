{% macro coalesce_empty(first_field, second_field) %}
    COALESCE(NULLIF({{first_field}}, ''), {{second_field}}, '')
{% endmacro %}