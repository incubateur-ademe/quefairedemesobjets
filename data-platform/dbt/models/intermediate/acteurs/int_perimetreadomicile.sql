-- dbt model

WITH perimetreadomicile AS (
    SELECT
        pad.acteur_id,
        pad.type,
        pad.valeur
    FROM {{ ref('base_perimetreadomicile') }} AS pad
    INNER JOIN
        {{ ref('int_acteur') }} AS a
        ON pad.acteur_id = a.identifiant_unique AND a.revision_existe = false
),

revisionperimetreadomicile AS (
    SELECT
        rpad.acteur_id,
        rpad.type,
        rpad.valeur
    FROM {{ ref('base_revisionperimetreadomicile') }} AS rpad
    INNER JOIN
        {{ ref('int_acteur') }} AS a
        ON rpad.acteur_id = a.identifiant_unique AND a.revision_existe = true
),

all_perimetreadomicile AS (
    SELECT * FROM perimetreadomicile
    UNION ALL
    SELECT * FROM revisionperimetreadomicile
)

SELECT
    pad.*,
    ROW_NUMBER() OVER (ORDER BY pad.acteur_id, pad.type, pad.valeur) AS id
FROM all_perimetreadomicile AS pad
