
SELECT
  identifiant_unique,
  nom,
  source_code,
  acteur_statut,
  revision_statut
FROM {{ ref('marts_acteur_revision') }}
WHERE revision_statut = 'ACTIF' AND acteur_statut != 'ACTIF'
