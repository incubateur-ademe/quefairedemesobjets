SELECT tva.*
FROM {{ ref('int_acteur') }} AS tva
LEFT JOIN {{ ref('int_acteur') }} AS tpva
    ON tva.parent_id = tpva.id
LEFT JOIN {{ ref('base_source') }} AS ts ON tva.source_id = ts.id
WHERE tva.statut = 'ACTIF'
    AND (tpva.statut is null or tpva.statut = 'ACTIF')
    AND ts.licence = 'OPEN_LICENSE' -- Only open lisense
    AND tva.public_accueilli NOT IN ('AUCUN', 'PROFESSIONNELS') -- AND va.public_accueilli != 'Professionnels' ?
    AND tva.id NOT LIKE '%_reparation_%'
