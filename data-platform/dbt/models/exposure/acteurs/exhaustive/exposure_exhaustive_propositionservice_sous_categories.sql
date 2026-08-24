select
    id,
    propositionservice_id as vuepropositionservice_id,
    souscategorieobjet_id
from {{ ref('marts_exhaustive_propositionservice_sous_categories') }}
