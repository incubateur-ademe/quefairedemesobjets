
SELECT a.identifiant_unique
FROM {{ ref('int_acteur_with_siret') }} a
INNER JOIN {{ ref('int_ae_siret_in_acteur') }} ae ON a.siret = ae.siret
WHERE ae.etat_administratif = 'A'
