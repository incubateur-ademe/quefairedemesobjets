SELECT
    vueacteur.identifiant_unique,
    vueacteur.siren,
    vueacteur.siret AS acteur_siret,
    lien_succession.siren_successeur,
    lien_succession.siret_successeur,
    lien_succession.etat_administratif_successeur,
    lien_succession.date_lien_succession,
    lien_succession.transfert_siege,
    lien_succession.continuite_economique
FROM {{ ref('int_ae_lien_succession_resolved') }} AS lien_succession
INNER JOIN {{ ref('base_vueacteur') }} AS vueacteur
    ON
        lien_succession.siret_predecesseur = vueacteur.siret
        AND (
            vueacteur.est_dans_carte IS TRUE
            OR vueacteur.est_dans_opendata IS TRUE
        )
WHERE lien_succession.etat_administratif_successeur = 'A'
