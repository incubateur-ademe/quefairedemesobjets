{{
  config(
    materialized = 'view',
    alias = 'marts_enrich_acteurs_villes_suggest_new',
    tags=['marts', 'enrich', 'villes', 'cities', 'ban', 'acteurs', 'nouvelle', 'new'],
  )
}}

SELECT
  '🌆 Changement de ville: 🟡 ancienne -> nouvelle' AS suggest_cohort,
  *
FROM {{ ref('marts_enrich_acteurs_villes_candidates') }}
WHERE udf_normalize_string_for_match(acteur_ville,3) != udf_normalize_string_for_match(suggest_ville,3)
AND ban_ville_ancienne IS NOT NULL