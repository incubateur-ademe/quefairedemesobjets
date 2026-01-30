{{
    config(
        materialized='incremental',
        unique_key='date_snapshot',
        incremental_strategy='delete+insert',
        tags=['exposure', 'stats', 'acteurs', 'visible', 'siret', 'actif']
    )
}}

SELECT
    CURRENT_DATE AS date_snapshot,
    CASE
        WHEN s.nombre_acteurs_visible_with_siret = 0 THEN 0
        ELSE ROUND((a.nb_acteur_visible_with_siret_actif::numeric / s.nombre_acteurs_visible_with_siret) * 100, 2)
    END AS taux_acteur_visible_with_siret_actif
FROM {{ ref('exposure_nb_acteur_visible_with_siret_history') }} s
CROSS JOIN {{ ref('exposure_nb_acteur_visible_with_siret_actif_history') }} a
WHERE s.date_snapshot = CURRENT_DATE
AND a.date_snapshot = CURRENT_DATE
