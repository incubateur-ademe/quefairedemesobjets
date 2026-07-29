SELECT propositionservice.*
FROM {{ ref('base_propositionservice') }} AS propositionservice
INNER JOIN
    {{ ref('int_acteur_with_revision') }} AS acteur
    ON propositionservice.acteur_id = acteur.identifiant_unique
