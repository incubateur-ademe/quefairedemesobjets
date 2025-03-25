-- depends_on: {{ ref('marts_carte_filtered_acteur') }}
-- depends_on: {{ ref('marts_carte_filtered_propositionservice') }}
-- depends_on: {{ ref('marts_carte_filtered_parentpropositionservice') }}

{{ propositionservice_sous_categories('marts_carte_filtered_acteur', 'marts_carte_filtered_propositionservice', 'marts_carte_filtered_parentpropositionservice')}}
