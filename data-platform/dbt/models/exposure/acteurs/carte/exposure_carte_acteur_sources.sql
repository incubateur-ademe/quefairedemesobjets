with data_ as (
    select
        acteur_id                                         as displayedacteur_id,
        source_id,
        ROW_NUMBER() over (order by acteur_id, source_id) as id
    from {{ ref('marts_carte_acteur_sources') }}
    group by acteur_id, source_id
)

select
    id,
    displayedacteur_id,
    source_id
from data_
