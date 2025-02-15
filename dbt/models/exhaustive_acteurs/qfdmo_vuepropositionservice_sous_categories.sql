

WITH propositionservice_sous_categories AS (
    SELECT
        pssscat.id AS id,
        ps.id AS vuepropositionservice_id,
        pssscat.souscategorieobjet_id AS souscategorieobjet_id
    FROM qfdmo_propositionservice_sous_categories pssscat
    INNER JOIN dbtvue_propositionservice AS ps ON CONCAT('PS_', pssscat.propositionservice_id) = ps.id AND ps.revision_existe = false
),
revisionpropositionservice_sous_categories AS (
    SELECT
        rpssscat.id AS id,
        ps.id AS vuepropositionservice_id,
        rpssscat.souscategorieobjet_id AS souscategorieobjet_id
    FROM qfdmo_revisionpropositionservice_sous_categories rpssscat
    JOIN dbtvue_propositionservice AS ps ON CONCAT('RPS_', rpssscat.revisionpropositionservice_id) = ps.id AND ps.revision_existe = true
)

SELECT * FROM propositionservice_sous_categories
UNION ALL
SELECT * FROM revisionpropositionservice_sous_categories
