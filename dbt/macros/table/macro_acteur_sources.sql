{%- macro acteur_sources(ephemeral_filtered_acteur, acteur ) -%}

WITH nochild_acteur_labels AS (
    SELECT
        a.identifiant_unique AS acteur_id,
        a.source_id AS source_id,
        a.identifiant_externe AS identifiant_externe
    FROM {{ ref(ephemeral_filtered_acteur) }} AS a
    WHERE a.parent_id is null AND a.source_id is not null
    GROUP BY a.identifiant_unique, a.source_id, a.identifiant_externe
),
parentacteur_labels AS (
    SELECT
        a.parent_id AS acteur_id,
        a.source_id AS source_id,
        a.identifiant_externe AS identifiant_externe
    FROM {{ ref(ephemeral_filtered_acteur) }} AS a
    WHERE a.parent_id is not null
    GROUP BY a.parent_id, a.source_id, a.identifiant_externe
),
acteur_sources AS (
    SELECT * FROM nochild_acteur_labels
    UNION ALL
    SELECT * FROM parentacteur_labels
)

SELECT ROW_NUMBER() OVER (ORDER BY acteur_id, s.source_id) AS id, s.*
FROM acteur_sources AS s
INNER JOIN {{ ref(acteur) }} AS a ON a.identifiant_unique = acteur_id

{%- endmacro -%}
