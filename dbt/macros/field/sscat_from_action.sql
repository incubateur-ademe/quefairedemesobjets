{% macro sscat_from_action(services, action) %}
  (
    SELECT string_agg(DISTINCT sc, '|')
    FROM jsonb_array_elements({{ services }}) as elem,
         jsonb_array_elements_text(elem->'sous_categories') as sc
    WHERE elem->>'action' = '{{ action }}'
  )
{% endmacro %}
