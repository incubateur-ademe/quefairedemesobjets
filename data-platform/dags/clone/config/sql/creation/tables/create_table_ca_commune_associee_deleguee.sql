/*
Schema table for « Contours Administratifs - Communes Associées et Déléguées »
*/

CREATE TABLE {{table_name}} (
    "id" INTEGER, -- 🟡 on reste scrict sur max (des IDs avec 16)
    "contours_administratifs" GEOMETRY(GEOMETRY, 4326), -- 🟡 geometry from geojson (accepts Polygon and MultiPolygon)
    "code" VARCHAR(5), -- 🟡 on reste scrict
    "nom" VARCHAR(100),
    "type" VARCHAR(20), -- commune-deleguee ou commune-associee
    "departement" VARCHAR(3),
    "region" VARCHAR(2),
    "epci" VARCHAR(9)
);
