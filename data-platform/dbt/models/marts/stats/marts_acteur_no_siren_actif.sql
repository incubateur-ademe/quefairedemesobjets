SELECT
  a.identifiant_unique,
  a.siren,
  ae.etat_administratif -- Null if not in AE
FROM {{ ref('int_acteur_with_siren') }} a
LEFT JOIN {{ ref('int_ae_siren_in_acteur') }} ae ON a.siren = ae.siren
WHERE LENGTH(a.siren) = 9
AND a.siren != '__empty__'
AND (ae.siren IS NULL OR ae.etat_administratif != 'A')
