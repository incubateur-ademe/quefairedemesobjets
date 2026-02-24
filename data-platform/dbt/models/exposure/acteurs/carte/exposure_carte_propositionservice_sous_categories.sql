select
    id,
    propositionservice_id AS displayedpropositionservice_id,
    souscategorieobjet_id
 from {{ ref('marts_carte_propositionservice_sous_categories') }}