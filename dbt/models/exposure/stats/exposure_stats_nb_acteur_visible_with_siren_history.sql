
SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nb_acteurs_visible_with_siren
FROM {{ ref('int_acteur_with_siren') }}
