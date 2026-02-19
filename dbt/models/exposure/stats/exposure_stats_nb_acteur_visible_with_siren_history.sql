-- DEPRECATED: will use exposure_stats_acteur_siren_siret_history instead

SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nb_acteurs_visible_with_siren
FROM {{ ref('int_acteur_with_siren') }}
