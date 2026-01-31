
SELECT ae.siret, ae.etat_administratif
FROM {{ source('stats_clone', 'clone_ae_etablissement_in_use') }} AS ae
INNER JOIN {{ ref('int_acteur_with_siret') }} AS av ON ae.siret = av.siret
GROUP BY ae.siret, ae.etat_administratif
