WITH propositionservice AS (
    SELECT
        CONCAT('PS_', ps.id::varchar)::varchar AS id,
        ps.acteur_id AS acteur_id,
        ps.action_id AS action_id,
        ps.id::integer AS ps_id,
        NULL::integer AS rps_id,
        false AS revision_existe
    FROM {{ ref('base_propositionservice') }} AS ps
    INNER JOIN {{ ref('int_acteur') }} AS a ON ps.acteur_id = a.identifiant_unique AND a.revision_existe = false
),
revisionpropositionservice AS (
    SELECT
        CONCAT('RPS_', rps.id::varchar)::varchar AS id,
        rps.acteur_id AS acteur_id,
        rps.action_id AS action_id,
        NULL::integer AS ps_id,
        rps.id::integer AS rps_id,
        true AS revision_existe
    FROM {{ ref('base_revisionpropositionservice') }} AS rps
    -- FIXME : test the INNER JOIN, is it necessary ?
    INNER JOIN {{ ref('int_acteur') }} AS a ON rps.acteur_id = a.identifiant_unique AND a.revision_existe = true
)

SELECT * FROM propositionservice
UNION ALL
SELECT * FROM revisionpropositionservice
