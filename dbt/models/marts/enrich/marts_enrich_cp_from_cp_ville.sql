{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'laposte', 'koumoul_epci', 'cp', 'ville'],
  )
}}

-- Get set of code postal and ville from acteurs that don't have a match with laposte_koumoul_cp_ville.code_postal
WITH acteurs_cp_ville_without_laposte_koumoul_cp_ville AS (
  SELECT
    code_postal,
    ville
  FROM {{ ref('marts_enrich_acteurs_cp_ville') }} AS acteurs_cp_ville
  LEFT JOIN {{ ref('int_laposte_koumoul_cp_ville') }} AS laposte ON laposte.base_code_postal = acteurs_cp_ville.code_postal
  WHERE laposte.base_code_postal IS NULL
), -- count 39369


cp_ville_without_laposte_koumoul_cp_ville_suggestions AS (
  SELECT
    acteurs.code_postal,
    acteurs.ville,
    base_cp_ville.base_code_postal AS suggest_code_postal,
    base_cp_ville.base_ville AS suggest_ville,
    SIMILARITY(UPPER(UNACCENT(REPLACE(acteurs.ville, ' CEDEX', ''))), UPPER(UNACCENT(base_cp_ville.base_ville))) AS similarity_score,
    ROW_NUMBER() OVER (
      PARTITION BY acteurs.code_postal, acteurs.ville
      ORDER BY SIMILARITY(UPPER(UNACCENT(REPLACE(acteurs.ville, ' CEDEX', ''))), UPPER(UNACCENT(base_cp_ville.base_ville))) DESC
    ) AS rank
  FROM acteurs_cp_ville_without_laposte_koumoul_cp_ville AS acteurs
  JOIN {{ ref('int_laposte_koumoul_cp_ville') }} AS base_cp_ville ON LEFT(base_cp_ville.base_code_postal, 2) = LEFT(acteurs.code_postal, 2)
  AND SIMILARITY(UPPER(UNACCENT(REPLACE(acteurs.ville, ' CEDEX', ''))), UPPER(UNACCENT(base_cp_ville.base_ville))) >= 0.7
)

SELECT
  ville,
  code_postal,
  suggest_ville,
  suggest_code_postal,
  similarity_score
FROM cp_ville_without_laposte_koumoul_cp_ville_suggestions
WHERE rank = 1

