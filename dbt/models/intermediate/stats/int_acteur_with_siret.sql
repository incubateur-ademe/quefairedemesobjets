-- on garde 4 chiffre après la virgule pour la latitude et la longitude
-- car 4 décimal ~11 m

SELECT identifiant_unique, siret
FROM {{ ref('base_vueacteur_visible') }}
WHERE LENGTH(siret) = 14
AND siret ~ '^[0-9]+$'
