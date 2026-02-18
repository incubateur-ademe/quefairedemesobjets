DROP VIEW IF EXISTS {{view_name}} CASCADE;
CREATE VIEW {{view_name}} AS (
    SELECT
        "#Code_commune_INSEE" AS code_commune_insee,
        "Nom_de_la_commune" AS nom_commune,
        "Code_postal" AS code_postal,
        "Libellé_d_acheminement" AS libellé_d_acheminement
    FROM {{table_name}}
)