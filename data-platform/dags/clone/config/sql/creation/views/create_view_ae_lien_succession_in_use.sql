/*
View to:
 - switch to the newly imported timestamped table
 - rename to under_score because camelCase breaks DBT
   (even double quoting both .sql and .yml in dbt, it gets ignored and breaks)
*/

-- Need to drop as schema has changed
DROP VIEW IF EXISTS {{view_name}} CASCADE;
CREATE VIEW {{view_name}} AS (
    SELECT
        "siretEtablissementPredecesseur" AS siret_predecesseur,
        "siretEtablissementSuccesseur" AS siret_successeur,
        "dateLienSuccession" AS date_lien_succession,
        "transfertSiege" AS transfert_siege,
        "continuiteEconomique" AS continuite_economique,
        "dateDernierTraitementLienSuccession" AS date_dernier_traitement
    FROM {{table_name}}
)
