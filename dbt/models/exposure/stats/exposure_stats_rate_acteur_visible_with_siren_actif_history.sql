
SELECT
    CURRENT_DATE AS date_snapshot,
    CASE
        WHEN s.nb_acteurs_visible_with_siren = 0 THEN 0
        ELSE ROUND((a.nb_acteur_visible_with_siren_actif::numeric / s.nb_acteurs_visible_with_siren) * 100, 2)
    END AS taux_acteur_visible_with_siren_actif
FROM {{ ref('exposure_stats_nb_acteur_visible_with_siren_history') }} s
CROSS JOIN {{ ref('exposure_stats_nb_acteur_visible_with_siren_actif_history') }} a
WHERE s.date_snapshot = CURRENT_DATE
AND a.date_snapshot = CURRENT_DATE
