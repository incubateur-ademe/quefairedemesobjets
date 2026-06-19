SELECT * FROM {{ ref('base_displayedperimetreadomicile') }}
WHERE acteur_id IN (SELECT identifiant_unique FROM {{ ref('marts_sample_displayedacteur') }})
