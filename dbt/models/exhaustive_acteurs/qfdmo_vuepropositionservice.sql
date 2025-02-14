WITH propositionservice AS (
    SELECT
        CONCAT('PS_', ps.id::text) as id,
        ps.acteur_id as acteur_id,
        ps.action_id as action_id,
        ps.id::integer as ps_id,
        NULL::integer as rps_id,
        false as revision_existe
    from qfdmo_propositionservice ps
    inner join dbtvue_acteur as a on ps.acteur_id = a.identifiant_unique and a.revision_existe = false
),
revisionpropositionservice AS (
    SELECT
        CONCAT('RPS_', rps.id::text) as id,
        rps.acteur_id as vueacteur_id,
        rps.action_id as action_id,
        NULL::integer as ps_id,
        rps.id::integer as rps_id,
        true as revision_existe
    from qfdmo_revisionpropositionservice rps
    join dbtvue_acteur as a on rps.acteur_id = a.identifiant_unique and a.revision_existe = true
)

SELECT * FROM propositionservice
UNION ALL
SELECT * FROM revisionpropositionservice
