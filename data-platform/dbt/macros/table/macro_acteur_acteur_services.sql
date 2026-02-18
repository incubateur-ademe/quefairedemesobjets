{%- macro acteur_acteur_services(ephemeral_filtered_acteur, acteur ) -%}

WITH nochild_acteur_acteur_services AS (
    SELECT
        aas.acteur_id AS acteur_id,
        aas.acteurservice_id AS acteurservice_id
    FROM {{ ref( 'int_acteur_acteur_services' )}} AS aas
    INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS a ON aas.acteur_id = a.identifiant_unique AND a.parent_id is null
    GROUP BY aas.acteur_id, aas.acteurservice_id
),
parentacteur_acteur_services AS (
    SELECT
        a.parent_id AS acteur_id,
        aas.acteurservice_id AS acteurservice_id
    FROM {{ ref( 'int_acteur_acteur_services' )}} AS aas
    INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS a ON aas.acteur_id = a.identifiant_unique AND a.parent_id is not null
    GROUP BY a.parent_id, aas.acteurservice_id
),
acteur_acteur_services AS (
    SELECT * FROM nochild_acteur_acteur_services
    UNION ALL
    SELECT * FROM parentacteur_acteur_services
)

SELECT ROW_NUMBER() OVER (ORDER BY acteur_id, aas.acteurservice_id) AS id, aas.*
FROM acteur_acteur_services AS aas
INNER JOIN {{ ref(acteur) }} AS a ON a.identifiant_unique = acteur_id

{%- endmacro -%}
