SELECT
    identifiant_unique,
    siren as siren_actuel,
    acteur_siret as siret_actuel,
    siren_successeur,
    siret_successeur,
    transfert_siege,
    continuite_economique
FROM {{ ref('marts_ae_lien_succession_resolved_vueacteur') }}
