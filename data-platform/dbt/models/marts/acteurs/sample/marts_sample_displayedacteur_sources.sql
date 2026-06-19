SELECT * FROM {{ ref('base_displayedacteur_sources') }}
WHERE displayedacteur_id IN (SELECT identifiant_unique FROM {{ ref('marts_sample_displayedacteur') }})
