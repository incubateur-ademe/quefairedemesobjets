
SELECT ae.siret, ae.etat_administratif
FROM {{ ref('base_ae_etablissement') }} AS ae
INNER JOIN {{ ref('int_acteur_with_siret') }} AS av ON ae.siret = av.siret
GROUP BY ae.siret, ae.etat_administratif
