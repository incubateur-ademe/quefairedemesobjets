-- depends_on: {{ ref('marts_opendata_filtered_acteur') }}
-- depends_on: {{ ref('marts_opendata_acteur') }}

{{ acteur_sources('marts_opendata_filtered_acteur', 'marts_opendata_acteur')}}
