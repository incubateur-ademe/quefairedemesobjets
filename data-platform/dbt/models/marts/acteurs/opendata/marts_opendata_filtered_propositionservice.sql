-- depends_on: {{ ref('marts_opendata_filtered_acteur') }}
-- depends_on: {{ ref('marts_opendata_filtered_parentpropositionservice') }}

{{ filtered_propositionservice('marts_opendata_filtered_acteur', 'marts_opendata_filtered_parentpropositionservice' )}}
