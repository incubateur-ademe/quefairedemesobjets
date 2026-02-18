SELECT
  acteur.identifiant_unique,
  acteur.nom,
  source.code AS source_code,
  acteur.statut AS acteur_statut,
  revision.statut AS revision_statut
FROM {{ ref('int_acteur_with_revision') }} AS acteur
INNER JOIN {{ ref('int_revision_with_acteur') }} AS revision
ON acteur.identifiant_unique = revision.identifiant_unique
LEFT JOIN {{ ref('base_source') }} AS source ON acteur.source_id = source.id