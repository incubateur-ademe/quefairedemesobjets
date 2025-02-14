

WITH propositionservice_sous_categories AS (
    SELECT
        pssscat.id as id,
        ps.id as vuepropositionservice_id,
        pssscat.souscategorieobjet_id as souscategorieobjet_id
    from qfdmo_propositionservice_sous_categories pssscat
    inner join dbtvue_propositionservice as ps on CONCAT('PS_', pssscat.propositionservice_id) = ps.id and ps.revision_existe = false
),
revisionpropositionservice_sous_categories AS (
    SELECT
        rpssscat.id as id,
        ps.id as vuepropositionservice_id,
        rpssscat.souscategorieobjet_id as souscategorieobjet_id
    from qfdmo_revisionpropositionservice_sous_categories rpssscat
    join dbtvue_propositionservice as ps on CONCAT('RPS_', rpssscat.revisionpropositionservice_id) = ps.id and ps.revision_existe = true
)

SELECT * FROM propositionservice_sous_categories
UNION ALL
SELECT * FROM revisionpropositionservice_sous_categories
