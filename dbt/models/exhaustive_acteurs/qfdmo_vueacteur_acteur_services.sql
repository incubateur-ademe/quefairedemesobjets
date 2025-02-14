WITH acteur_acteur_services AS (
    SELECT
        al.id as id,
        al.acteur_id as vueacteur_id,
        al.acteurservice_id as acteurservice_id
    from qfdmo_acteur_acteur_services al
    inner join dbtvue_acteur as a on al.acteur_id = a.identifiant_unique and a.revision_existe = false
),
revisionacteur_acteur_services AS (
    SELECT
        ral.id as id,
        ral.revisionacteur_id as vueacteur_id,
        ral.acteurservice_id as acteurservice_id
    from qfdmo_revisionacteur_acteur_services ral
    join dbtvue_acteur as a on ral.revisionacteur_id = a.identifiant_unique and a.revision_existe = true
)

SELECT * FROM acteur_acteur_services
UNION ALL
SELECT * FROM revisionacteur_acteur_services
