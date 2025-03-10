-- depends_on: {{ ref('marts_opendata_filtered_propositionservice') }}
-- depends_on: {{ ref('marts_opendata_propositionservice_sous_categories') }}

{{ propositionservice('marts_opendata_filtered_propositionservice', 'marts_opendata_propositionservice_sous_categories')}}
