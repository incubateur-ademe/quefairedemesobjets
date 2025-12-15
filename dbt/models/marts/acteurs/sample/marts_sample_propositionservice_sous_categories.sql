SELECT * FROM {{ source('qfdmo', 'qfdmo_displayedpropositionservice_sous_categories') }}
WHERE displayedpropositionservice_id IN (SELECT id FROM {{ ref('marts_sample_propositionservice') }})
