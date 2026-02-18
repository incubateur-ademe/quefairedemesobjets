select
    id,
    acteur_id AS vueacteur_id,
    acteurservice_id
 from {{ ref('marts_exhaustive_acteur_acteur_services') }}