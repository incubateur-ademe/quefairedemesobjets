SELECT * FROM {{ ref('base_displayedpropositionservice_sous_categories') }}
WHERE displayedpropositionservice_id IN (SELECT id FROM {{ ref('marts_sample_displayedpropositionservice') }})
