SELECT
    vueacteur.identifiant_unique,
    vueacteur.siren,
    vueacteur.siret as acteur_siret,
    siren_successeur,
    siret_successeur,
    etat_administratif_successeur,
    date_lien_succession,
    transfert_siege,
    continuite_economique
FROM {{ ref('int_ae_lien_succession_resolved') }}
INNER JOIN {{ source('stats_qfdmo', 'qfdmo_vueacteur') }} AS vueacteur
ON vueacteur.siret = siret_predecesseur
AND (vueacteur.est_dans_carte IS TRUE OR vueacteur.est_dans_opendata IS TRUE)
WHERE etat_administratif_successeur = 'A'
