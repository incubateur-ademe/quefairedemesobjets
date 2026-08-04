SELECT a.identifiant_unique
FROM {{ ref('int_acteur_with_siret') }} AS a
INNER JOIN
    {{ ref('int_ae_siret_in_acteur') }} AS ae
    ON a.siret = ae.siret AND ae.etat_administratif = 'A'
