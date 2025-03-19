{%- macro acteur_acteur_services(ephemeral_filtered_acteur, acteur ) -%}

WITH nochild_acteur_acteur_services AS (
    SELECT
        aas.vueacteur_id AS acteur_id,
        aas.acteurservice_id AS acteurservice_id
    FROM qfdmo_vueacteur_acteur_services aas
    INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS a ON aas.vueacteur_id = a.id AND a.parent_id is null
    GROUP BY aas.vueacteur_id, aas.acteurservice_id
),
parentacteur_acteur_services AS (
    SELECT
        a.parent_id AS acteur_id,
        aas.acteurservice_id AS acteurservice_id
    FROM qfdmo_vueacteur_acteur_services aas
    INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS a ON aas.vueacteur_id = a.id AND a.parent_id is not null
    GROUP BY a.parent_id, aas.acteurservice_id
),
acteur_acteur_services AS (
    SELECT * FROM nochild_acteur_acteur_services
    UNION ALL
    SELECT * FROM parentacteur_acteur_services
)

SELECT ROW_NUMBER() OVER (ORDER BY acteur_id, aas.acteurservice_id) AS id, aas.*
FROM acteur_acteur_services AS aas
INNER JOIN {{ ref(acteur) }} AS a ON a.id = acteur_id

{%- endmacro -%}
