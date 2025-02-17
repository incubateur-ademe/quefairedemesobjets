WITH acteur_labels AS (
    SELECT
        MIN(al.id) AS id,
        al.acteur_id AS vueacteur_id,
        al.labelqualite_id AS labelqualite_id
    FROM qfdmo_acteur_labels al
    INNER JOIN {{ ref('qfdmo_vueacteur') }} AS a ON al.acteur_id = a.identifiant_unique AND a.revision_existe = false
    GROUP BY al.acteur_id, al.labelqualite_id
),
revisionacteur_labels AS (
    SELECT
        MIN(ral.id) AS id,
        ral.revisionacteur_id AS vueacteur_id,
        ral.labelqualite_id AS labelqualite_id
    FROM qfdmo_revisionacteur_labels ral
    INNER JOIN {{ ref('qfdmo_vueacteur') }} AS a ON ral.revisionacteur_id = a.identifiant_unique AND a.revision_existe = true
    GROUP BY ral.revisionacteur_id, ral.labelqualite_id
)

SELECT * FROM acteur_labels
UNION ALL
SELECT * FROM revisionacteur_labels