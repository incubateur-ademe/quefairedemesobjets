
SELECT *
FROM {{ ref('base_vuepropositionservice') }} AS propositionservice
INNER JOIN {{ ref('base_vueacteur_visible') }} AS acteur ON propositionservice.acteur_id = acteur.identifiant_unique