-- We keep 4 decimal places for the latitude and longitude
-- because 4 decimal places ~11 meters

SELECT identifiant_unique, latitude, longitude
FROM {{ ref('base_vueacteur_visible') }}
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
AND latitude != 0 AND longitude != 0
