-- DEPRECATED: will use exposure_stats_acteur_stacked_history instead of
-- exposure_stats_rate_acteur_stacked_history and exposure_stats_nb_acteur_stacked_rounded_history

WITH stacked AS (
    SELECT COUNT(*) AS nb_acteurs_stacked
    FROM {{ ref('marts_acteur_stacked_rounded') }}
),
visible AS (
    SELECT COUNT(*) AS nb_acteurs_visible_with_location
    FROM {{ ref('int_acteur_visible_location') }}
)
SELECT
    CURRENT_DATE AS date_snapshot,
    s.nb_acteurs_stacked,
    v.nb_acteurs_visible_with_location,
    CASE
        WHEN v.nb_acteurs_visible_with_location = 0 THEN 0
        ELSE ROUND((s.nb_acteurs_stacked::NUMERIC / v.nb_acteurs_visible_with_location) * 100, 2)
    END AS rate_acteur_stacked_rounded
FROM stacked s
CROSS JOIN visible v
