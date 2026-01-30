-- on garde 4 chiffre après la virgule pour la latitude et la longitude
-- car 4 décimal ~11 m

SELECT identifiant_unique, siren
FROM {{ ref('base_acteur_visible') }}
WHERE LENGTH(siren) = 9
AND siret ~ '^[0-9]+$'
