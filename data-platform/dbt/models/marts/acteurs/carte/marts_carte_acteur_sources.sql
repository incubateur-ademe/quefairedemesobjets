-- depends_on: {{ ref('marts_carte_filtered_acteur') }}
-- depends_on: {{ ref('marts_carte_acteur') }}

{{ acteur_sources('marts_carte_filtered_acteur', 'marts_carte_acteur')}}
