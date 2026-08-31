SELECT propositionservice_sous_categories.*
FROM
    {{ ref('base_propositionservice_sous_categories') }}
        AS propositionservice_sous_categories
INNER JOIN
    {{ ref('int_propositonservices_with_revision') }} AS propositionservice
    ON
        propositionservice_sous_categories.propositionservice_id
        = propositionservice.id
