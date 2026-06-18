
SELECT ae.siren, ae.etat_administratif
FROM {{ ref('base_ae_unite_legale') }} AS ae
INNER JOIN {{ ref('int_acteur_with_siren') }} AS av ON ae.siren = av.siren
GROUP BY ae.siren, ae.etat_administratif
