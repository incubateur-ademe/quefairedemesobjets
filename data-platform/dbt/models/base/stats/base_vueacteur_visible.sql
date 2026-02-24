
SELECT *
FROM {{ source('stats_qfdmo', 'qfdmo_vueacteur') }}
WHERE est_dans_carte IS TRUE OR est_dans_opendata IS TRUE
{% if env_var('DBT_SAMPLING', 'false') == 'true' %}
TABLESAMPLE SYSTEM (10)
{% endif %}
