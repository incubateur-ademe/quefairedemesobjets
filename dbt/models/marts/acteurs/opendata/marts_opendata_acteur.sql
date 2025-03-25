-- depends_on: {{ ref('marts_opendata_filtered_acteur') }}
-- depends_on: {{ ref('marts_opendata_propositionservice')}}

{{ acteur('marts_opendata_filtered_acteur', 'marts_opendata_propositionservice')}}
