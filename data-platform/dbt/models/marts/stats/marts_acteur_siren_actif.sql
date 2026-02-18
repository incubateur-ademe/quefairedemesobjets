
SELECT a.identifiant_unique
FROM {{ ref('int_acteur_with_siren') }} a
INNER JOIN {{ ref('int_ae_siren_in_acteur') }} ae ON a.siren = ae.siren
WHERE ae.etat_administratif = 'A'
