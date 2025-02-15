with parent_propositionservice AS (
    SELECT
    concat(pps.parent_id::text, '_', pps.action_id::text) AS id,
    pps.parent_id AS acteur_id,
    pps.action_id AS action_id
    FROM {{ ref('temp_parentpropositionservice') }} AS pps
    group by 2,3
),
nochild_propositionservice AS (
    SELECT
    vps.id AS id,
    vps.acteur_id AS acteur_id,
    vps.action_id AS action_id
    FROM qfdmo_vuepropositionservice AS vps
    INNER JOIN {{ ref('temp_cartefilteredacteur') }} AS cfa
        ON vps.acteur_id = cfa.identifiant_unique AND cfa.parent_id is null
)

SELECT * FROM parent_propositionservice
union all
SELECT * FROM nochild_propositionservice
