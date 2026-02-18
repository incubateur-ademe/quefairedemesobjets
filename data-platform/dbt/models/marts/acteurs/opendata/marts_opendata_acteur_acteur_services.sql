-- depends_on: {{ ref('marts_opendata_filtered_acteur') }}
-- depends_on: {{ ref('marts_opendata_acteur') }}

{{ acteur_acteur_services('marts_opendata_filtered_acteur', 'marts_opendata_acteur')}}
