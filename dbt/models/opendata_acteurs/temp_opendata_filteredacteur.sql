SELECT tva.*
FROM qfdmo_vueacteur AS tva
LEFT JOIN qfdmo_vueacteur AS tpva
    ON tva.parent_id = tpva.identifiant_unique
LEFT JOIN qfdmo_source AS ts ON tva.source_id = ts.id
WHERE tva.statut = 'ACTIF'
    AND (tpva.statut is null or tpva.statut = 'ACTIF')
    AND ts.licence = 'OPEN_LICENSE' -- Only open lisense
    AND tva.public_accueilli NOT IN ('AUCUN', 'PROFESSIONNELS') -- AND va.public_accueilli != 'Professionnels' ?
    AND tva.identifiant_unique NOT LIKE '%_reparation_%'
