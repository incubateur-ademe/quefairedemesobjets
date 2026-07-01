-- We keep 4 decimal places for the latitude and longitude
-- because 4 decimal places ~11 meters

SELECT identifiant_unique, siren, siret, code_postal, ville
FROM {{ ref('int_acteur_with_siret') }}
WHERE siren = ''
