SELECT
  '🌆 Changement de ville: 🟢 variation d''ortographe' AS suggest_cohort,
  *
FROM {{ ref('marts_enrich_acteurs_villes_candidates') }}
WHERE {{ target.schema }}.udf_normalize_string_for_match(acteur_ville,3) = {{ target.schema }}.udf_normalize_string_for_match(suggest_ville,3)
AND ban_ville_ancienne IS NULL
