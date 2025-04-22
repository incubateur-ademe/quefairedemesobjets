select
    id,
    propositionservice_id AS vuepropositionservice_id,
    souscategorieobjet_id
from {{ ref('marts_exhaustive_propositionservice_sous_categories') }}