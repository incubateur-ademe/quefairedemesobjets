
SELECT rounded_latitude, rounded_longitude
FROM {{ ref('int_acteur_visible_location_rounded') }}
GROUP BY rounded_latitude, rounded_longitude
HAVING COUNT(*) > 1
