SELECT a.identifiant_unique
FROM {{ ref('int_acteur_with_siren') }} AS a
INNER JOIN
    {{ ref('int_ae_siren_in_acteur') }} AS ae
    ON a.siren = ae.siren AND ae.etat_administratif = 'A'
