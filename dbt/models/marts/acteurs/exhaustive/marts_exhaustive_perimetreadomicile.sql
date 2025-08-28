-- depends_on: {{ ref('marts_carte_acteur') }}
-- depends_on: {{ ref('int_perimetreadomicile') }}

SELECT * FROM {{ ref('int_perimetreadomicile') }}
