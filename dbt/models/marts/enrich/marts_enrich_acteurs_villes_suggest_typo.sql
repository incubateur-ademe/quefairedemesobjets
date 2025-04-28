{{
  config(
    materialized = 'view',
    alias = 'marts_enrich_acteurs_villes_suggest_typo',
    tags=['marts', 'enrich', 'ville', 'ban','acteurs','typo','ortographe'],
  )
}}

SELECT
  '🌆 Changement de ville: 🟢 variation d''ortographe' AS suggest_cohort,
  *
FROM {{ ref('marts_enrich_acteurs_villes_candidates') }}
WHERE udf_normalize_string_for_match(acteur_ville,3) = udf_normalize_string_for_match(suggest_ville,3)
AND ban_ville_ancienne IS NULL
