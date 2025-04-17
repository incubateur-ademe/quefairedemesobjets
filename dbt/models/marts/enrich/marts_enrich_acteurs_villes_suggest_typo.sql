{{
  config(
    materialized = 'view',
    alias = 'marts_enrich_acteurs_villes_suggest_typo',
    tags=['marts', 'enrich', 'ville', 'ban','acteurs','typo','ortographe'],
  )
}}

SELECT
  'acteurs_villes_variation_ortographe' AS suggestion_cohorte_code,
  '🌆 Changement de ville: 🟢 variation d''ortographe' AS suggestion_cohorte_label,
  *
FROM {{ ref('marts_enrich_acteurs_villes_suggest') }}
WHERE udf_normalize_string_for_match(acteur_ville,3) = udf_normalize_string_for_match(remplacer_ville,3)
AND ban_ville_ancienne IS NULL
