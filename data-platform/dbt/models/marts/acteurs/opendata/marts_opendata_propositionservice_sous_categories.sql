-- depends_on: {{ ref('marts_opendata_filtered_acteur') }}
-- depends_on: {{ ref('marts_opendata_filtered_propositionservice') }}
-- depends_on: {{ ref('marts_opendata_filtered_parentpropositionservice') }}

{{ propositionservice_sous_categories('marts_opendata_filtered_acteur', 'marts_opendata_filtered_propositionservice', 'marts_opendata_filtered_parentpropositionservice')}}
