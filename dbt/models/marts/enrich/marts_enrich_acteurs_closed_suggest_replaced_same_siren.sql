{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'closed', 'ae', 'annuaire_entreprises', 'etablissement'],
  )
}}

SELECT
  'acteurs_closed_replaced_same_siren' AS suggestion_cohorte_code,
  '🚪 Acteurs Fermés: 🟢 remplacés par SIRET du même SIREN' AS suggestion_cohorte_label,
  *
FROM {{ ref('marts_enrich_acteurs_closed_replaced') }}
WHERE suggest_siret_is_from_same_siren IS TRUE
