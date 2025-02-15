WITH acteur_acteur_services AS (
    SELECT
        al.id AS id,
        al.acteur_id AS vueacteur_id,
        al.acteurservice_id AS acteurservice_id
    FROM qfdmo_acteur_acteur_services al
    INNER JOIN dbtvue_acteur AS a ON al.acteur_id = a.identifiant_unique AND a.revision_existe = false
),
revisionacteur_acteur_services AS (
    SELECT
        ral.id AS id,
        ral.revisionacteur_id AS vueacteur_id,
        ral.acteurservice_id AS acteurservice_id
    FROM qfdmo_revisionacteur_acteur_services ral
    JOIN dbtvue_acteur AS a ON ral.revisionacteur_id = a.identifiant_unique AND a.revision_existe = true
)

SELECT * FROM acteur_acteur_services
UNION ALL
SELECT * FROM revisionacteur_acteur_services
