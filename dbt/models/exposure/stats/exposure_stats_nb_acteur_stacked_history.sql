-- DEPRECATED: will use exposure_stats_acteur_stacked_history instead of
-- exposure_stats_rate_acteur_stacked_history and exposure_stats_nb_acteur_stacked_history


SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nb_acteurs_stacked
FROM {{ ref('marts_acteur_stacked') }}
