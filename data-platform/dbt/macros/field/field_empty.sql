{% macro field_empty(field) %}
    CASE WHEN {{ field }} = '__empty__' THEN '' ELSE {{ field }} END
{% endmacro %}