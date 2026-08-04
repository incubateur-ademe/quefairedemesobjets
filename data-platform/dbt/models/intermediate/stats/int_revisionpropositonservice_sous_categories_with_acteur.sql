SELECT revisionpropositionservice_sous_categories.*
FROM
    {{ ref('base_revisionpropositionservice_sous_categories') }}
        AS revisionpropositionservice_sous_categories
INNER JOIN
    {{ ref('int_revisionpropositonservices_with_acteur') }}
        AS revisionpropositionservice
    ON
        revisionpropositionservice_sous_categories.revisionpropositionservice_id
        = revisionpropositionservice.id
