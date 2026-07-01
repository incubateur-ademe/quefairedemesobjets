-- We keep 4 decimal places for the latitude and longitude
-- because 4 decimal places ~11 meters

SELECT identifiant_unique, siret, siren, code_postal, ville
FROM {{ ref('base_vueacteur_visible') }}
WHERE LENGTH(siret) = 14
AND siret ~ '^[0-9]+$'
