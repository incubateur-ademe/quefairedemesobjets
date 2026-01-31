-- on garde 4 chiffre après la virgule pour la latitude et la longitude
-- car 4 décimal ~11 m

SELECT identifiant_unique, latitude, longitude
FROM {{ ref('base_acteur_visible') }}
WHERE latitude IS NOT NULL AND longitude IS NOT NULL
AND latitude != 0 AND longitude != 0
