SELECT a.identifiant_unique, a.siret
FROM {{ ref('int_acteur_with_siret') }} a
LEFT JOIN {{ ref('int_ae_siret_in_acteur') }} ae ON a.siret = ae.siret and ae.etat_administratif = 'A'
WHERE ae.siret IS NULL
AND LENGTH(a.siret) = 14
