
SELECT propositionservice_sous_categories.* FROM {{ ref('base_propositionservice_sous_categories') }} AS propositionservice_sous_categories
INNER JOIN {{ ref('int_propositonservices_with_revision') }} as propositionservice ON propositionservice.id = propositionservice_sous_categories.propositionservice_id
