/*
Schema table for « Contours Administratifs - Régions »
*/

CREATE TABLE {{table_name}} (
    "id" INTEGER, -- 🟡 on reste scrict sur max (des IDs avec 16)
    "contours_administratifs" GEOMETRY(GEOMETRY, 4326), -- 🟡 geometry from geojson (accepts Polygon and MultiPolygon)
    "code" VARCHAR(2), -- 🟡 on reste scrict (code région)
    "nom" VARCHAR(100)
);
