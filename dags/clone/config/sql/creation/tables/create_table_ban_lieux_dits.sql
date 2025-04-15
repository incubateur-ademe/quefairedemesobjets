/*
Schema generated by scripts/db_schema_create_from_csv.py
*/

CREATE TABLE {{table_name}} (
  "id" VARCHAR(12), -- 🟡 on reste scrict (min/max=10/12)
  "nom_lieu_dit" VARCHAR(125), -- 98 -> 125
  "code_postal" CHAR(5), -- 🟡 on reste scrict (min/max=5)
  "code_insee" CHAR(5), -- 🟡 on reste scrict (min/max=5)
  "nom_commune" VARCHAR(60), -- 45 -> 60
  "code_insee_ancienne_commune" CHAR(5), -- 🟡 on reste scrict (min/max=5)
  "nom_ancienne_commune" VARCHAR(60), -- 29 -> 60
  "x" FLOAT4,
  "y" FLOAT4,
  "lon" FLOAT4,
  "lat" FLOAT4,
  "source_position" VARCHAR(15),  -- 8 -> 15
  "source_nom_voie" VARCHAR(15)    -- 8 -> 15
);