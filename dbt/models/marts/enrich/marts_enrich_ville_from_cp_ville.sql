{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'cp', 'ville', 'suggestions', 'laposte', 'koumoul_epci'],
  )
}}

-- Get set of code postal and ville from acteurs that don't have a match in laposte_koumoul_cp_ville
WITH acteurs_cp_ville_without_laposte_koumoul_cp_ville AS (
  SELECT
    code_postal,
    ville
  FROM {{ ref('marts_enrich_acteurs_cp_ville') }} AS acteurs_cp_ville
  WHERE (code_postal, ville) NOT IN (SELECT base_code_postal, base_ville FROM {{ ref('int_laposte_koumoul_cp_ville') }})
), -- count 39369

-- Get and sort suggestions
cp_ville_without_koumoul_epci_ville_suggestions AS (
  SELECT
    cp_ville.*,
    laposte.base_ville AS suggest_ville,
    SIMILARITY(UPPER(UNACCENT(cp_ville.ville)), UPPER(UNACCENT(laposte.base_ville))) AS similarity_score,
    ROW_NUMBER() OVER (PARTITION BY cp_ville.code_postal, cp_ville.ville ORDER BY SIMILARITY(REPLACE(UPPER(UNACCENT(cp_ville.ville)), ' CEDEX', ''), UPPER(UNACCENT(laposte.base_ville))) DESC) AS rank
  FROM acteurs_cp_ville_without_laposte_koumoul_cp_ville AS cp_ville
  JOIN {{ ref('int_laposte_koumoul_cp_ville') }} AS laposte ON laposte.base_code_postal = cp_ville.code_postal
)

SELECT
  code_postal,
  ville,
  suggest_ville,
  similarity_score
FROM cp_ville_without_koumoul_epci_ville_suggestions AS acteurs
WHERE rank = 1
