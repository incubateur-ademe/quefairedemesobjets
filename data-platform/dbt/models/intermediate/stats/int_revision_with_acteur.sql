SELECT revision.* FROM {{ ref('base_revisionacteur') }} as revision
INNER JOIN {{ ref('base_acteur') }} as acteur ON revision.identifiant_unique = acteur.identifiant_unique
WHERE revision.identifiant_unique IS NOT NULL