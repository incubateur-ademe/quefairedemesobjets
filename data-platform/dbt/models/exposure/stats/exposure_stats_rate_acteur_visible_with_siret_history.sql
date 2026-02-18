-- DEPRECATED: will use exposure_stats_acteur_siren_siret_history instead

SELECT
    CURRENT_DATE AS date_snapshot,
    CASE
        WHEN v.nb_acteurs_visible = 0 THEN 0
        ELSE ROUND((s.nb_acteurs_visible_with_siret::numeric / v.nb_acteurs_visible) * 100, 2)
    END AS taux_acteur_visible_with_siret
FROM {{ ref('exposure_stats_nb_acteur_visible_history') }} v
CROSS JOIN {{ ref('exposure_stats_nb_acteur_visible_with_siret_history') }} s
WHERE v.date_snapshot = CURRENT_DATE
AND s.date_snapshot = CURRENT_DATE
