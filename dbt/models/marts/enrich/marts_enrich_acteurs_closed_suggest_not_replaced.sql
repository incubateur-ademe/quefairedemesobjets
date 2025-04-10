/*
Acteurs which SIREN & SIRET are closed in AE's etablissement
AND for which we couldn't find replacements
*/
{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'closed', 'ae', 'annuaire_entreprises', 'etablissement'],
  )
}}

SELECT
  'acteurs_closed_not_replaced' AS suggestion_cohorte_code,
  '🚪 Acteurs Fermés: 🔴 non remplacés' AS suggestion_cohorte_label,
  *
FROM {{ ref('marts_enrich_acteurs_closed_candidates') }}
WHERE
  /* In candidates we already filter on etab_est_actif IS FALSE
  but we don't filter on unite_est_actif IS FALSE
  because it would prevent us from finding replacements for same unite,
  however for acteurs we consider fully closed we do apply that filter */
  unite_est_actif is FALSE
  AND acteur_id NOT IN (
    SELECT acteur_id FROM {{ ref('marts_enrich_acteurs_closed_replaced') }}
  )

