with data_ as (
    select
        acteur_id                                         as vueacteur_id,
        source_id,
        ROW_NUMBER() over (order by acteur_id, source_id) as id
    from {{ ref('marts_exhaustive_acteur_sources') }}
    group by acteur_id, source_id
)

select
    id,
    vueacteur_id,
    source_id
from
    data_
