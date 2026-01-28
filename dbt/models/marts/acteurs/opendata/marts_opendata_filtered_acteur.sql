
WITH filtered_children_acteur AS (
    SELECT tva.*
    FROM {{ ref('int_acteur') }} AS tva
    LEFT JOIN {{ ref('int_acteur') }} AS tpva
    ON tva.parent_id = tpva.identifiant_unique
LEFT JOIN {{ ref('base_source') }} AS ts ON tva.source_id = ts.id
WHERE tva.statut = 'ACTIF'
    AND (tpva.statut is null or tpva.statut = 'ACTIF')
    AND ts.licence = 'OPEN_LICENSE' -- Only open lisense
),
filtered_parent_acteur AS (
    SELECT tva.*
    FROM {{ ref('int_acteur') }} AS tva
    WHERE tva.identifiant_unique IN (SELECT parent_id FROM filtered_children_acteur)
)

SELECT * FROM filtered_parent_acteur
UNION ALL
SELECT * FROM filtered_children_acteur

