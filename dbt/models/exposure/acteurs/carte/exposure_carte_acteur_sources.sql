select
    id,
    acteur_id AS displayedacteur_id,
    source_id
 from {{ ref('marts_carte_acteur_sources') }}