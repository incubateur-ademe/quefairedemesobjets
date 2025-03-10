-- depends_on: {{ ref('marts_carte_filtered_propositionservice') }}
-- depends_on: {{ ref('marts_carte_propositionservice_sous_categories') }}

{{ propositionservice('marts_carte_filtered_propositionservice', 'marts_carte_propositionservice_sous_categories')}}
