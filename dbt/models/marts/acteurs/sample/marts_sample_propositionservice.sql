SELECT * FROM {{ source('qfdmo', 'qfdmo_displayedpropositionservice') }}
WHERE acteur_id IN (SELECT identifiant_unique FROM {{ ref('marts_sample_acteur') }})