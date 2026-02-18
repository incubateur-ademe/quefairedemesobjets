-- replace :
--   exposure_stats_rate_acteur_stacked_history
--   exposure_stats_nb_acteur_stacked_history
--   exposure_stats_nb_acteur_stacked_rounded_history
--   exposure_stats_rate_acteur_stacked_rounded_history

WITH stacked AS (
    SELECT COUNT(*) AS nb_stacked
    FROM {{ ref('marts_acteur_stacked') }}
),
stacked_rounded AS (
    SELECT COUNT(*) AS nb_stacked_rounded
    FROM {{ ref('marts_acteur_stacked_rounded') }}
),
visible AS (
    SELECT COUNT(*) AS nb_total
    FROM {{ ref('int_acteur_visible_location') }}
)
SELECT
    CURRENT_DATE AS date_snapshot,
    v.nb_total, -- visible & with_location
    s.nb_stacked,
    sr.nb_stacked_rounded,
    CASE
        WHEN v.nb_total = 0 THEN 0
        ELSE ROUND((s.nb_stacked::NUMERIC / v.nb_total) * 100, 2)
    END AS rate_stacked,
    CASE
        WHEN v.nb_total = 0 THEN 0
        ELSE ROUND((sr.nb_stacked_rounded::NUMERIC / v.nb_total) * 100, 2)
    END AS rate_stacked_rounded
FROM visible v
CROSS JOIN stacked s
CROSS JOIN stacked_rounded sr
