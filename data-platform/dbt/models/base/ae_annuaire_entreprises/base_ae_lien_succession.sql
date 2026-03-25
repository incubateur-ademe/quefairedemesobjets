/*
Notes:
 - Cast transfert_siege and continuite_economique to boolean
 - Joining with etablissement to avoid none existing siret
*/

SELECT
    siret_predecesseur,
    etab_predecesseur.etat_administratif as etat_administratif_predecesseur,
    etab_successeur.siren as siren_successeur,
    siret_successeur,
    etab_successeur.etat_administratif as etat_administratif_successeur,
    date_lien_succession,
    transfert_siege::boolean AS transfert_siege,
    continuite_economique::boolean AS continuite_economique
FROM {{ source('ae', 'clone_ae_lien_succession_in_use') }}
INNER JOIN {{ ref('base_ae_etablissement') }} AS etab_predecesseur ON etab_predecesseur.siret = siret_predecesseur AND etab_predecesseur.etat_administratif != 'A'
INNER JOIN {{ ref('base_ae_etablissement') }} AS etab_successeur ON etab_successeur.siret = siret_successeur
