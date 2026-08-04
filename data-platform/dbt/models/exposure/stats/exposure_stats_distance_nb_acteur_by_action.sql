-- Statistiques de distance et nombre de solutions par action
-- Calcule la moyenne de distance_m et nb_solutions_100km par action + global

WITH stats_par_action AS (
    SELECT
        base_action.id
            AS action_id,
        base_action.code
            AS action_code,
        ROUND(AVG(distance_first_action.distance_m)::numeric, 2)
            AS avg_distance_m,
        ROUND(AVG(distance_first_action.nb_solutions_100km)::numeric, 2)
            AS avg_nb_solutions_100km,
        COUNT(*)
            AS nb_positions
    FROM {{ ref('marts_distance_first_action') }} AS distance_first_action
    INNER JOIN {{ ref('base_action') }} AS base_action
        ON distance_first_action.action_id = base_action.id
    GROUP BY base_action.id, base_action.code
),

stats_global AS (
    SELECT
        NULL::integer                              AS action_id,
        'TOUTES_ACTIONS'                           AS action_code,
        ROUND(AVG(distance_m)::numeric, 2)         AS avg_distance_m,
        ROUND(AVG(nb_solutions_100km)::numeric, 2) AS avg_nb_solutions_100km,
        COUNT(*)                                   AS nb_positions
    FROM {{ ref('marts_distance_first_action') }}
)

SELECT
    CURRENT_DATE AS date_snapshot,
    *
FROM stats_par_action

UNION ALL

SELECT
    CURRENT_DATE AS date_snapshot,
    *
FROM stats_global
