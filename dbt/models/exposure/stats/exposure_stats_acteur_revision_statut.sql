SELECT
  *
FROM {{ ref('marts_acteur_revision_statut') }}
WHERE revision_statut = 'ACTIF' AND acteur_statut != 'ACTIF'