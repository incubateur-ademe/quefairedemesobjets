{{
  config(
    materialized = 'view',
    alias = 'marts_enrich_acteurs_villes_suggest_other',
    tags=['marts', 'enrich', 'ville', 'ban','acteurs','nouvelle','other'],
  )
}}

SELECT
  'acteurs_villes_other' AS suggestion_cohorte_code,
  '🌆 Changement de ville: 🔴 autre' AS suggestion_cohorte_label,
  *
FROM {{ ref('marts_enrich_acteurs_villes_suggest') }}
WHERE udf_normalize_string_for_match(acteur_ville,3) != udf_normalize_string_for_match(suggest_ville,3)
AND ban_ville_ancienne IS NULL