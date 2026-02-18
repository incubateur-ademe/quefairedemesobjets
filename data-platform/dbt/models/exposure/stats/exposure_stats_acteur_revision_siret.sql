
SELECT
  identifiant_unique,
  nom,
  source_code,
  acteur_siret,
  revision_siret,
  acteur_modifie_le,
  revision_modifie_le
FROM {{ ref('marts_acteur_revision') }}
WHERE revision_siret != ''
AND acteur_siret != ''
AND acteur_statut = 'ACTIF'
AND revision_statut = 'ACTIF'
AND revision_siret != acteur_siret
AND revision_modifie_le < acteur_modifie_le
