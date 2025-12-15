SELECT * FROM {{ source('qfdmo', 'qfdmo_displayedacteur_acteur_services') }}
WHERE displayedacteur_id IN (SELECT identifiant_unique FROM {{ ref('marts_sample_acteur') }})