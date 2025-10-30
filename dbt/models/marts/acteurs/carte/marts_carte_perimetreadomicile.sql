-- depends_on: {{ ref('marts_carte_acteur') }}
-- depends_on: {{ ref('int_perimetreadomicile') }}

{{ perimetreadomicile('marts_carte_filtered_acteur') }}
