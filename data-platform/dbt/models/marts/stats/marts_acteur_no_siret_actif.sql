SELECT
  a.identifiant_unique,
  a.siret,
  ae.etat_administratif -- Null if not in AE
FROM {{ ref('int_acteur_with_siret') }} a
LEFT JOIN {{ ref('int_ae_siret_in_acteur') }} ae ON a.siret = ae.siret
WHERE LENGTH(a.siret) = 14
AND (ae.siret IS NULL OR ae.etat_administratif != 'A')
