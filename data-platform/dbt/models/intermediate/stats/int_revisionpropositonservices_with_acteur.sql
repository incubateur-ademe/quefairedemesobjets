
SELECT revisionpropositionservice.* FROM {{ ref('base_revisionpropositionservice') }} AS revisionpropositionservice
INNER JOIN {{ ref('int_revision_with_acteur') }} as revision ON revisionpropositionservice.acteur_id = revision.identifiant_unique
