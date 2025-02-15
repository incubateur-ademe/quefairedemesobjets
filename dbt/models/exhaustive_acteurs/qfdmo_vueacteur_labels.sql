WITH acteur_labels AS (
    SELECT
        al.id AS id,
        al.acteur_id AS vueacteur_id,
        al.labelqualite_id AS labelqualite_id
    FROM qfdmo_acteur_labels al
    INNER JOIN dbtvue_acteur AS a ON al.acteur_id = a.identifiant_unique AND a.revision_existe = false
),
revisionacteur_labels AS (
    SELECT
        ral.id AS id,
        ral.revisionacteur_id AS vueacteur_id,
        ral.labelqualite_id AS labelqualite_id
    FROM qfdmo_revisionacteur_labels ral
    JOIN dbtvue_acteur AS a ON ral.revisionacteur_id = a.identifiant_unique AND a.revision_existe = true
)

SELECT * FROM acteur_labels
UNION ALL
SELECT * FROM revisionacteur_labels