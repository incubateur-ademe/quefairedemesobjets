
SELECT
  identifiant_unique,
  nom,
  source_code,
  acteur_siren,
  revision_siren,
  acteur_modifie_le,
  revision_modifie_le
FROM {{ ref('marts_acteur_revision') }}
WHERE revision_siren != ''
AND acteur_siren != ''
AND acteur_statut = 'ACTIF'
AND revision_statut = 'ACTIF'
AND revision_siren != acteur_siren
AND revision_modifie_le < acteur_modifie_le
