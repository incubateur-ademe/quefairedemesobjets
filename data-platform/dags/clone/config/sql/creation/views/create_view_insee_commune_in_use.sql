DROP VIEW IF EXISTS {{view_name}} CASCADE;
CREATE VIEW {{view_name}} AS (
    SELECT
        "TYPECOM" AS type_de_commune, -- 🟡 on reste scrict : COM ou COMD
        "COM" AS code_commune, -- 🟡 on reste scrict
        "REG" AS code_region, -- 🟡 on reste scrict
        "DEP" AS code_departement, -- 🟡 on reste scrict
        "CTCD" AS code_canton, -- 🟡 on reste scrict
        "ARR" AS code_arrondissement, -- 🟡 on reste scrict
        "TNCC" AS type_nom_en_clair, -- 🟡 on reste scrict
        "NCC" AS nom_commune_simple, -- 🟡 on reste scrict
        "NCCENR" AS nom_commune_enrichi, -- 🟡 on reste scrict
        "LIBELLE" AS nom_commune, -- 100 -> 150
        "CAN" AS can, -- 🟡 on reste scrict
        "COMPARENT" AS code_commune_parente -- 🟡 on reste scrict
     FROM {{table_name}}
)