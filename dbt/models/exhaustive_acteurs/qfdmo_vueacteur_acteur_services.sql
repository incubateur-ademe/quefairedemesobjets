WITH acteur_acteur_services AS (
    SELECT
        MIN(al.id) AS id,
        al.acteur_id AS vueacteur_id,
        al.acteurservice_id AS acteurservice_id
    FROM qfdmo_acteur_acteur_services al
    INNER JOIN {{ ref('temp_filteredacteur') }} AS a ON al.acteur_id = a.identifiant_unique AND a.revision_existe = false
    GROUP BY al.acteur_id, al.acteurservice_id
),
revisionacteur_acteur_services AS (
    SELECT
        MIN(ral.id) AS id,
        ral.revisionacteur_id AS vueacteur_id,
        ral.acteurservice_id AS acteurservice_id
    FROM qfdmo_revisionacteur_acteur_services ral
    INNER JOIN {{ ref('temp_filteredacteur') }} AS a ON ral.revisionacteur_id = a.identifiant_unique AND a.revision_existe = true
    GROUP BY ral.revisionacteur_id, ral.acteurservice_id
)

SELECT * FROM acteur_acteur_services
UNION ALL
SELECT * FROM revisionacteur_acteur_services
