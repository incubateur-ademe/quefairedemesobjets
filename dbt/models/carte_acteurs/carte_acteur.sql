SELECT DISTINCT va.*
FROM {{ ref('temp_filteredacteur') }} AS va
INNER JOIN {{ ref('carte_propositionservice') }} AS cps
    ON va.identifiant_unique = cps.acteur_id
