select
    id,
    acteur_id AS displayedacteur_id,
    acteurservice_id
 from {{ ref('marts_carte_acteur_acteur_services') }}