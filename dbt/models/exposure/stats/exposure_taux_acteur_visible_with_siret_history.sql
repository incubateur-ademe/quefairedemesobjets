{{
    config(
        materialized='incremental',
        unique_key='date_snapshot',
        incremental_strategy='delete+insert',
        tags=['exposure', 'stats', 'acteurs', 'visible', 'siret']
    )
}}

SELECT
    CURRENT_DATE AS date_snapshot,
    CASE
        WHEN v.nombre_acteurs_visible = 0 THEN 0
        ELSE ROUND((s.nombre_acteurs_visible_with_siret::numeric / v.nombre_acteurs_visible) * 100, 2)
    END AS taux_acteur_visible_with_siret
FROM {{ ref('exposure_nb_acteur_visible_history') }} v
CROSS JOIN {{ ref('exposure_nb_acteur_visible_with_siret_history') }} s
WHERE v.date_snapshot = CURRENT_DATE
AND s.date_snapshot = CURRENT_DATE
