select
    id,
    acteur_id as displayedacteur_id,
    labelqualite_id
from {{ ref('marts_carte_acteur_labels') }}
