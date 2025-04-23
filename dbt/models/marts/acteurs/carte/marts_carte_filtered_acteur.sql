SELECT tva.*
FROM {{ ref('int_acteur') }} AS tva
LEFT JOIN {{ ref('int_acteur') }} AS tpva
    ON tva.parent_id = tpva.identifiant_unique
WHERE tva.statut = 'ACTIF'
    AND (tpva.statut is null or tpva.statut = 'ACTIF')