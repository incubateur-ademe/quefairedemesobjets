SELECT a.identifiant_unique, a.siren
FROM {{ ref('int_acteur_with_siren') }} a
LEFT JOIN {{ ref('int_ae_siren_in_acteur') }} ae ON a.siren = ae.siren and ae.etat_administratif = 'A'
WHERE ae.siren IS NULL
AND LENGTH(a.siren) = 9
AND a.siren != '__empty__'
