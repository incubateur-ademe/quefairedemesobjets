SELECT acteur.* FROM {{ ref('base_acteur') }} AS acteur
INNER JOIN
    {{ ref('base_revisionacteur') }} AS revision
    ON acteur.identifiant_unique = revision.identifiant_unique
WHERE revision.identifiant_unique IS NOT NULL AND revision.statut = 'ACTIF'
