SELECT tva.*
FROM qfdmo_vueacteur AS tva
LEFT JOIN qfdmo_vueacteur AS tpva
    ON tva.parent_id = tpva.identifiant_unique
WHERE tva.statut = 'ACTIF'
    AND (tpva.statut is null or tpva.statut = 'ACTIF') -- AND va.public_accueilli != 'Professionnels'
