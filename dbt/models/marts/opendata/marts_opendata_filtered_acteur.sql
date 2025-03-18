
WITH filtered_children_acteur AS (
    SELECT tva.*
    FROM {{ ref('int_acteur') }} AS tva
    LEFT JOIN {{ ref('int_acteur') }} AS tpva
    ON tva.parent_id = tpva.identifiant_unique
LEFT JOIN {{ ref('base_source') }} AS ts ON tva.source_id = ts.id
WHERE tva.statut = 'ACTIF'
    AND (tpva.statut is null or tpva.statut = 'ACTIF')
    AND ts.licence = 'OPEN_LICENSE' -- Only open lisense
    AND tva.public_accueilli NOT IN ('AUCUN', 'PROFESSIONNELS') -- AND va.public_accueilli != 'Professionnels' ?
    AND tva.identifiant_unique NOT LIKE '%_reparation_%'
    AND tva.nom='VELOPITO'
),
filtered_parent_acteur AS (
    SELECT tva.*
    FROM {{ ref('int_acteur') }} AS tva
    WHERE tva.identifiant_unique IN (SELECT parent_id FROM filtered_children_acteur)
)

SELECT * FROM filtered_parent_acteur
UNION ALL
SELECT * FROM filtered_children_acteur

