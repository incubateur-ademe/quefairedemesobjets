select
    id,
    acteur_id AS vueacteur_id,
    labelqualite_id
 from {{ ref('marts_exhaustive_acteur_labels') }}