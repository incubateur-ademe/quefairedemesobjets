select * from {{ source('qfdmo', 'qfdmo_acteur') }}
{% if env_var('DBT_SAMPLING', 'false') == 'true' %}
TABLESAMPLE SYSTEM (10)
{% endif %}
