
SELECT a.identifiant_unique, a.latitude, a.longitude
FROM {{ ref('int_acteur_visible_location') }} a
INNER JOIN {{ ref('int_stacked_location') }} c
    ON a.latitude = c.latitude
    AND a.longitude = c.longitude
ORDER BY a.latitude, a.longitude, a.identifiant_unique
