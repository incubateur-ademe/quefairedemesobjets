
SELECT propositionservice.* FROM {{ ref('base_propositionservice') }} AS propositionservice
INNER JOIN {{ ref('int_acteur_with_revision') }} as acteur ON propositionservice.acteur_id = acteur.identifiant_unique
