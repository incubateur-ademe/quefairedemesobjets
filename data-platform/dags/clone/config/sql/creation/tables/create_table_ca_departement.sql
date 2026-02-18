/*
Schema table for « Contours Administratifs - Départements »
*/

CREATE TABLE {{table_name}} (
    "id" INTEGER, -- 🟡 on reste scrict sur max (des IDs avec 16)
    "contours_administratifs" GEOMETRY(GEOMETRY, 4326), -- 🟡 geometry from geojson (accepts Polygon and MultiPolygon)
    "code" VARCHAR(3), -- 🟡 on reste scrict (2 ou 3 caractères pour départements)
    "nom" VARCHAR(100),
    "region" VARCHAR(2)
);
