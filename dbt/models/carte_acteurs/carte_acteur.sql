SELECT DISTINCT va.*
FROM qfdmo_vueacteur AS va
INNER JOIN {{ ref('carte_propositionservice') }} AS cps
    ON va.identifiant_unique = cps.acteur_id
