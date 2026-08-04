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
),

final AS (

    SELECT
        v.nb_total,
        s.nb_stacked, -- visible & with_location
        sr.nb_stacked_rounded,
        CURRENT_DATE AS date_snapshot,
        CASE
            WHEN v.nb_total = 0 THEN 0
            ELSE ROUND((s.nb_stacked::NUMERIC / v.nb_total) * 100, 2)
        END          AS rate_stacked,
        CASE
            WHEN v.nb_total = 0 THEN 0
            ELSE ROUND((sr.nb_stacked_rounded::NUMERIC / v.nb_total) * 100, 2)
        END          AS rate_stacked_rounded
    FROM visible AS v
    CROSS JOIN stacked AS s
    CROSS JOIN stacked_rounded AS sr
)

SELECT
    date_snapshot,
    nb_total,
    nb_stacked,
    nb_stacked_rounded,
    rate_stacked,
    rate_stacked_rounded
FROM final
