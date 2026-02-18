{%- macro propositionservice_sous_categories(ephemeral_filtered_acteur, ephemeral_filtered_propositionservice, ephemeral_filtered_parentpropositionservice ) -%}

with
    parent_propositionservice_sous_categories
    AS
    (
        SELECT
            CONCAT(pps.parent_id::varchar, '_', pps.action_id::varchar)::varchar AS propositionservice_id,
            pssscat.souscategorieobjet_id AS souscategorieobjet_id
        FROM {{ ref("int_propositionservice_sous_categories") }} AS pssscat
            INNER JOIN {{ ref(ephemeral_filtered_parentpropositionservice) }} AS pps
                ON pps.id = pssscat.propositionservice_id
        GROUP BY
            pps.parent_id,
            pps.action_id,
            pssscat.souscategorieobjet_id
    ),
    nochild_propositionservice_sous_categories
    AS
    (
        SELECT
            pssscat.propositionservice_id AS propositionservice_id,
            pssscat.souscategorieobjet_id AS souscategorieobjet_id
        FROM {{ ref("int_propositionservice_sous_categories") }} AS pssscat
            INNER JOIN {{ ref(ephemeral_filtered_propositionservice) }} AS ps ON pssscat.propositionservice_id = ps.id
            INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS cfa ON ps.acteur_id = cfa.identifiant_unique AND cfa.parent_id is null
        GROUP BY
            pssscat.propositionservice_id,
            pssscat.souscategorieobjet_id
    ),
    propositionservice_sous_categories
    AS
    (
        SELECT *
            FROM parent_propositionservice_sous_categories
        UNION ALL
        SELECT *
            FROM nochild_propositionservice_sous_categories
    )

SELECT ROW_NUMBER() OVER (ORDER BY propositionservice_id, souscategorieobjet_id) AS id, *
FROM propositionservice_sous_categories

{%- endmacro -%}
