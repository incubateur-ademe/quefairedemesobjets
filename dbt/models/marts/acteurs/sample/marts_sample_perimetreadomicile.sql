-- depends_on: {{ ref('marts_carte_acteur') }}
-- depends_on: {{ ref('int_perimetreadomicile') }}

SELECT * FROM {{ source('qfdmo', 'qfdmo_displayedperimetreadomicile') }}
WHERE acteur_id IN (SELECT identifiant_unique FROM {{ ref('marts_sample_acteur') }})
