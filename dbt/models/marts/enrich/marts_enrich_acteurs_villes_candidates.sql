{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'villes', 'cities', 'ban'],
  )
}}

SELECT
  acteurs.identifiant_unique AS acteur_id,
  acteurs.ville AS acteur_ville,
  acteurs.code_postal AS acteur_code_postal,
  acteurs.statut AS acteur_statut,
  ban.ville_ancienne AS ban_ville_ancienne,
  ban.ville AS ban_ville,
  ban.code_postal AS ban_code_postal,
  ban.ville AS suggest_ville
FROM {{ ref('marts_carte_acteur') }} AS acteurs
JOIN {{ ref('int_ban_villes') }} AS ban ON ban.code_postal = acteurs.code_postal
WHERE acteurs.statut = 'ACTIF'
AND acteurs.code_postal IS NOT NULL and acteurs.code_postal != '' and LENGTH(acteurs.code_postal) = 5
/* Only suggest if 1 difference */
AND (
  acteurs.ville != ban.ville_ancienne
  OR acteurs.ville != ban.ville
)
/* BUT also a match somewhere */
AND (
  udf_normalize_string_for_match(acteurs.ville,3) = udf_normalize_string_for_match(ban.ville_ancienne,3)
  OR udf_normalize_string_for_match(acteurs.ville,3) = udf_normalize_string_for_match(ban.ville,3)
)
