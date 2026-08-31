SELECT
    a.identifiant_unique,
    a.latitude,
    a.longitude
FROM {{ ref('int_acteur_visible_location') }} AS a
INNER JOIN {{ ref('int_stacked_location') }} AS c
    ON
        a.latitude = c.latitude
        AND a.longitude = c.longitude
ORDER BY a.latitude, a.longitude, a.identifiant_unique
