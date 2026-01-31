
SELECT ae.siren, ae.etat_administratif
FROM {{ source('stats_clone', 'clone_ae_unite_legale_in_use') }} AS ae
INNER JOIN {{ ref('int_acteur_with_siren') }} AS av ON ae.siren = av.siren
GROUP BY ae.siren, ae.etat_administratif
