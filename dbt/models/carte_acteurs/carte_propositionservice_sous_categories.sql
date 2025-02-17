with
    parent_vuepropositionservice_sous_categories
    AS
    (
        SELECT
            MIN(qfdmo_vuepropositionservice_sous_categories.id) AS id,
            CONCAT(temp_parentpropositionservice.parent_id::text, '_', temp_parentpropositionservice.action_id::text) AS propositionservice_id,
            qfdmo_vuepropositionservice_sous_categories.souscategorieobjet_id AS souscategorieobjet_id
        FROM qfdmo_vuepropositionservice_sous_categories
            INNER JOIN {{ ref('temp_parentpropositionservice') }} AS temp_parentpropositionservice
                ON temp_parentpropositionservice.id = qfdmo_vuepropositionservice_sous_categories.vuepropositionservice_id
        GROUP BY
            propositionservice_id,
            souscategorieobjet_id
    ),
    nochild_vuepropositionservice_sous_categories
    AS
    (
        SELECT
            qfdmo_vuepropositionservice_sous_categories.id AS id,
            qfdmo_vuepropositionservice_sous_categories.vuepropositionservice_id AS propositionservice_id,
            qfdmo_vuepropositionservice_sous_categories.souscategorieobjet_id AS souscategorieobjet_id
        FROM qfdmo_vuepropositionservice_sous_categories
            INNER JOIN {{ ref('temp_propositionservice') }} AS ps ON qfdmo_vuepropositionservice_sous_categories.vuepropositionservice_id = ps.id
            INNER JOIN {{ ref('temp_filteredacteur') }} AS cfa ON ps.acteur_id = cfa.identifiant_unique AND cfa.parent_id is null
    )

SELECT *
    FROM parent_vuepropositionservice_sous_categories
UNION ALL
SELECT *
    FROM nochild_vuepropositionservice_sous_categories
