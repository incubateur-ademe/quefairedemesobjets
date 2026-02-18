
SELECT latitude, longitude
FROM {{ ref('int_acteur_visible_location') }}
GROUP BY latitude, longitude
HAVING COUNT(*) > 1
