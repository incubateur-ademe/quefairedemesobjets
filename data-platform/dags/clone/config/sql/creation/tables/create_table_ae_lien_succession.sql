/*
Schema based on INSEE SIRENE documentation for StockEtablissementLiensSuccession
cf. https://www.sirene.fr/static-resources/documentation/v_sommaire_311.htm
 - Strict on ID-like fields (e.g. siret)
 - Loose on other fields to avoid pipeline failures for variable data
 - VARCHAR for the same reason we don't control the data
 - {{table_name}} so that no one can run this by mistake AND
    to facilitate table name replacement in Python
*/

CREATE TABLE {{table_name}} (
  "siretEtablissementPredecesseur" VARCHAR(14), -- 🟡 on reste strict
  "siretEtablissementSuccesseur" VARCHAR(14), -- 🟡 on reste strict
  "dateLienSuccession" VARCHAR(10), -- 🟡 on reste strict (AAAA-MM-JJ)
  "transfertSiege" VARCHAR(5), -- boolean-like
  "continuiteEconomique" VARCHAR(5), -- boolean-like
  "dateDernierTraitementLienSuccession" VARCHAR(30) -- 19 -> 30 (AAAA-MM-JJTHH:MM:SS)
);
