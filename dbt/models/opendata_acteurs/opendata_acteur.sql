SELECT DISTINCT va.*
FROM {{ ref('temp_opendata_filteredacteur') }} AS va
INNER JOIN {{ ref('opendata_propositionservice') }} AS cps
    ON va.identifiant_unique = cps.acteur_id
