/*
Extract set of code postal and ville from acteurs

*/
{{
  config(
    materialized = 'view',
    tags=['marts', 'enrich', 'acteurs', 'cp', 'ville'],
  )
}}

SELECT
    code_postal,
    ville
FROM {{ source('enrich', 'qfdmo_vueacteur') }} AS acteurs
WHERE acteurs.statut = 'ACTIF'
AND (acteurs.est_dans_carte IS TRUE OR acteurs.est_dans_opendata IS TRUE)
AND acteurs.code_postal IS NOT NULL and acteurs.code_postal != '' and LENGTH(acteurs.code_postal) = 5
GROUP BY code_postal, ville
