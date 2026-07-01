SELECT
    av.identifiant_unique,
    ae.siren,
    ae.siret,
    ae.code_postal
FROM {{ ref('int_acteur_with_siret_without_siren') }} AS av
INNER JOIN {{ ref('base_ae_etablissement') }} AS ae
    ON ae.siret = av.siret
WHERE ae.etat_administratif = 'A'
