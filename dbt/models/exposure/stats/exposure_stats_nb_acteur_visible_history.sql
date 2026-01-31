
SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nb_acteurs_visible
FROM {{ ref('base_acteur_visible') }}
