WITH norevacteur_acteur_services AS (
    SELECT
        aas.acteur_id AS acteur_id,
        aas.acteurservice_id AS acteurservice_id
    FROM {{ ref('base_acteur_acteur_services') }} AS aas
    INNER JOIN {{ ref('int_acteur') }} AS a ON aas.acteur_id = a.identifiant_unique AND a.revision_existe = false
    GROUP BY aas.acteur_id, aas.acteurservice_id
),
revisionacteur_acteur_services AS (
    SELECT
        raas.revisionacteur_id AS acteur_id,
        raas.acteurservice_id AS acteurservice_id
    FROM {{ ref('base_revisionacteur_acteur_services') }} AS raas
    INNER JOIN {{ ref('int_acteur') }} AS a ON raas.revisionacteur_id = a.identifiant_unique AND a.revision_existe = true
    GROUP BY raas.revisionacteur_id, raas.acteurservice_id
),
acteur_acteur_services AS (
    SELECT * FROM norevacteur_acteur_services
    UNION ALL
    SELECT * FROM revisionacteur_acteur_services
)

SELECT ROW_NUMBER() OVER (ORDER BY acteur_id, acteurservice_id) AS id, * FROM acteur_acteur_services