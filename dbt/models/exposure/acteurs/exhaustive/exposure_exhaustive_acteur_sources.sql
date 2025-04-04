select
    id,
    acteur_id AS vueacteur_id,
    source_id
from {{ ref('marts_exhaustive_acteur_sources') }}