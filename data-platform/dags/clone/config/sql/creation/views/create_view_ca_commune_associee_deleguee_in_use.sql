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
        "code" AS code_commune,
        "nom" AS nom_commune,
        "type" AS type_commune,
        "departement" AS code_departement,
        "region" AS code_region,
        "epci" AS code_epci
    FROM {{table_name}}
)
