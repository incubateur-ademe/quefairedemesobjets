SELECT acteur.* FROM {{ ref('base_acteur') }} as acteur
INNER JOIN {{ ref('base_revisionacteur') }} as revision ON acteur.identifiant_unique = revision.identifiant_unique
WHERE revision.identifiant_unique IS NOT NULL