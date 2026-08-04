/*
Acteurs which SIREN & SIRET are closed in AE's etablissement
AND for which we couldn't find replacements
*/
SELECT
    candidates.*,
    '🚪 Acteurs Fermés: 🔴 non remplacés - unité fermée' AS suggest_cohort
FROM {{ ref('marts_enrich_acteurs_closed_candidates') }} AS candidates
WHERE
    /* In candidates we already filter on etab_est_actif IS FALSE
    but we don't filter on unite_est_actif IS FALSE
    because it would prevent us from finding replacements for same unite,
    however for acteurs we consider fully closed we do apply that filter */
    candidates.unite_est_actif IS FALSE
    AND candidates.acteur_id NOT IN (
        SELECT replaced.acteur_id
        FROM {{ ref('marts_enrich_acteurs_closed_replaced') }} AS replaced
    )
