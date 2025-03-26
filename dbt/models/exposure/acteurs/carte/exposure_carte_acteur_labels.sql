select
    id,
    acteur_id AS displayedacteur_id,
    labelqualite_id
 from {{ ref('marts_carte_acteur_labels') }}