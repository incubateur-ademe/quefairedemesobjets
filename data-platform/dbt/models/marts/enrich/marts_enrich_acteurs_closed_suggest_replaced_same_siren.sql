SELECT
  '🚪 Acteurs Fermés: 🟢 remplacés par SIRET du même SIREN' AS suggest_cohort,
  *
FROM {{ ref('marts_enrich_acteurs_closed_replaced') }}
WHERE suggest_siret_is_from_same_siren IS TRUE
