WITH nochild_acteur_labels AS (
    SELECT
        al.vueacteur_id AS acteur_id,
        al.labelqualite_id AS labelqualite_id
    FROM qfdmo_vueacteur_labels al
    INNER JOIN {{ ref('temp_opendata_filteredacteur') }} AS a ON al.vueacteur_id = a.identifiant_unique AND a.parent_id is null
    GROUP BY al.vueacteur_id, al.labelqualite_id
),
parentacteur_labels AS (
    SELECT
        a.parent_id AS acteur_id,
        al.labelqualite_id AS labelqualite_id
    FROM qfdmo_vueacteur_labels al
    INNER JOIN {{ ref('temp_opendata_filteredacteur') }} AS a ON al.vueacteur_id = a.identifiant_unique AND a.parent_id is not null
    GROUP BY a.parent_id, al.labelqualite_id
),
acteur_labels AS (
    SELECT * FROM nochild_acteur_labels
    UNION ALL
    SELECT * FROM parentacteur_labels
)

SELECT ROW_NUMBER() OVER (ORDER BY acteur_id, al.labelqualite_id) AS id, al.*
FROM acteur_labels AS al
INNER JOIN {{ ref('opendata_acteur') }} AS a ON a.identifiant_unique = acteur_id