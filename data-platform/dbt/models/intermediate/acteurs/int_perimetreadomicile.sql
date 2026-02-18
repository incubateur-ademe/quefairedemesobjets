-- dbt model

WITH perimetreadomicile AS (
    SELECT
        pad.acteur_id AS acteur_id,
        pad.type AS type,
        pad.valeur AS valeur
    FROM {{ ref('base_perimetreadomicile') }} AS pad
    INNER JOIN {{ ref('int_acteur') }} AS a ON pad.acteur_id = a.identifiant_unique AND a.revision_existe = false
),
revisionperimetreadomicile AS (
    SELECT
        rpad.acteur_id AS acteur_id,
        rpad.type AS type,
        rpad.valeur AS valeur
    FROM {{ ref('base_revisionperimetreadomicile') }} AS rpad
    INNER JOIN {{ ref('int_acteur') }} AS a ON rpad.acteur_id = a.identifiant_unique AND a.revision_existe = true
),
all_perimetreadomicile AS (
    SELECT * FROM perimetreadomicile
    UNION ALL
    SELECT * FROM revisionperimetreadomicile
)

SELECT ROW_NUMBER() OVER (ORDER BY acteur_id, type, valeur) AS id, pad.*
FROM all_perimetreadomicile AS pad
