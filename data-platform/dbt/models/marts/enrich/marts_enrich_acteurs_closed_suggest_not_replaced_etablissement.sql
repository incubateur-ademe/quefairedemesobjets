/*
Acteurs which SIREN & SIRET are closed in AE's etablissement
AND for which we couldn't find replacements
*/
SELECT
  '🚪 Acteurs Fermés: 🔴 non remplacés - établissement fermé' AS suggest_cohort,
  *
FROM {{ ref('marts_enrich_acteurs_closed_candidates') }}
WHERE
  /* In candidates we already filter on etab_est_actif IS FALSE
  but we don't filter on unite_est_actif IS FALSE
  because it would prevent us from finding replacements for same unite,
  however for acteurs we consider fully closed we do apply that filter */
  acteur_id NOT IN (
    SELECT acteur_id FROM {{ ref('marts_enrich_acteurs_closed_suggest_not_replaced_unite') }}
  )
  AND acteur_id NOT IN (
    SELECT acteur_id FROM {{ ref('marts_enrich_acteurs_closed_replaced') }}
  )
