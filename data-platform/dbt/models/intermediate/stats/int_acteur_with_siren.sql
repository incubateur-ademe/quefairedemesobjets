-- We keep 4 decimal places for the latitude and longitude
-- because 4 decimal places ~11 meters

SELECT identifiant_unique, siren
FROM {{ ref('base_vueacteur_visible') }}
WHERE LENGTH(siren) = 9
AND siret ~ '^[0-9]+$'
