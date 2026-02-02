
SELECT a.identifiant_unique, a.rounded_latitude, a.rounded_longitude
FROM {{ ref('int_acteur_visible_location_rounded') }} a
INNER JOIN {{ ref('int_stacked_location_rounded') }} c
    ON a.rounded_latitude = c.rounded_latitude
    AND a.rounded_longitude = c.rounded_longitude
ORDER BY a.rounded_latitude, a.rounded_longitude, a.identifiant_unique
