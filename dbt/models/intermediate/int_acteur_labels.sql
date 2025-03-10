WITH norevacteur_labels AS (
    SELECT
        al.acteur_id AS acteur_id,
        al.labelqualite_id AS labelqualite_id
    FROM {{ ref('base_acteur_labels') }} AS al
    -- We can't use the base_acteur table because it doesn't have the revision_existe column
    INNER JOIN {{ ref('int_acteur') }} AS a ON al.acteur_id = a.identifiant_unique AND a.revision_existe = false
),
revisionacteur_labels AS (
    SELECT
        ral.revisionacteur_id AS acteur_id,
        ral.labelqualite_id AS labelqualite_id
    FROM {{ ref('base_revisionacteur_labels') }} AS ral
    -- We can't use the base_acteur table because it doesn't have the revision_existe column
    INNER JOIN {{ ref('int_acteur') }} AS a ON ral.revisionacteur_id = a.identifiant_unique AND a.revision_existe = true
),
acteur_labels AS (
    SELECT * FROM norevacteur_labels
    UNION ALL
    SELECT * FROM revisionacteur_labels
)

SELECT ROW_NUMBER() OVER (ORDER BY acteur_id, labelqualite_id) AS id, *
FROM acteur_labels
