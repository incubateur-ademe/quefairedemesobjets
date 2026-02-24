
SELECT
  acteur.identifiant_unique,
  acteur.nom,
  source.code AS source_code,
  acteur.siren AS acteur_siren,
  acteur.siret AS acteur_siret,
  acteur.statut AS acteur_statut,
  acteur.modifie_le AS acteur_modifie_le,
  revision.siren AS revision_siren,
  revision.siret AS revision_siret,
  revision.statut AS revision_statut,
  revision.modifie_le AS revision_modifie_le
FROM {{ ref('int_acteur_with_revision') }} AS acteur
INNER JOIN {{ ref('int_revision_with_acteur') }} AS revision
ON acteur.identifiant_unique = revision.identifiant_unique
LEFT JOIN {{ ref('base_source') }} AS source ON acteur.source_id = source.id
