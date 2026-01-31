
SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nb_acteurs_stacked
FROM {{ ref('marts_acteur_stacked_rounded') }}
