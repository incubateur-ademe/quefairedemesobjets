/*
Notes:
 - Cast transfert_siege and continuite_economique to boolean
 - Joining with etablissement to avoid none existing siret
*/

SELECT
    lien_succession.siret_predecesseur,
    etab_predecesseur.etat_administratif
        AS etat_administratif_predecesseur,
    etab_successeur.siren                          AS siren_successeur,
    lien_succession.siret_successeur,
    etab_successeur.etat_administratif
        AS etat_administratif_successeur,
    lien_succession.date_lien_succession,
    lien_succession.transfert_siege::boolean       AS transfert_siege,
    lien_succession.continuite_economique::boolean AS continuite_economique
FROM {{ source('ae', 'clone_ae_lien_succession_in_use') }} AS lien_succession
INNER JOIN
    {{ ref('base_ae_etablissement') }} AS etab_predecesseur
    ON
        lien_succession.siret_predecesseur = etab_predecesseur.siret
        AND etab_predecesseur.etat_administratif != 'A'
INNER JOIN
    {{ ref('base_ae_etablissement') }} AS etab_successeur
    ON lien_succession.siret_successeur = etab_successeur.siret
