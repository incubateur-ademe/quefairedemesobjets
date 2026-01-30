SELECT ae.siret, ae.etat_administratif
FROM {{ source('stats_clone', 'clone_ae_etablissement_in_use') }} AS ae
INNER JOIN {{ ref('base_acteur_visible') }} AS av ON ae.siren = av.siren
