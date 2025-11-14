-- depends_on: {{ ref('marts_carte_filtered_acteur') }}
-- depends_on: {{ ref('marts_carte_propositionservice')}}

{{ acteur('marts_carte_filtered_acteur', 'marts_carte_propositionservice', 'marts_carte_acteur_epci')}}
