
SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nb_acteurs_visible_with_siret
FROM {{ ref('int_acteur_with_siret') }}
