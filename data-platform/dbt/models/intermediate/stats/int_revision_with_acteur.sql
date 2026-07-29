SELECT revision.* FROM {{ ref('base_revisionacteur') }} AS revision
INNER JOIN
    {{ ref('base_acteur') }} AS acteur
    ON revision.identifiant_unique = acteur.identifiant_unique
WHERE revision.identifiant_unique IS NOT NULL
