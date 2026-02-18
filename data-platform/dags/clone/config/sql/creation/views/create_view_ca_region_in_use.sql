/*
View to:
 - switch to the newly imported timestamped table
*/

-- Need to drop as schema has changed
DROP VIEW IF EXISTS {{view_name}} CASCADE;
CREATE VIEW {{view_name}} AS (
    SELECT
        "id" AS id,
        "contours_administratifs" AS contours_administratifs,
        "code" AS code_region,
        "nom" AS nom_region
    FROM {{table_name}}
)
