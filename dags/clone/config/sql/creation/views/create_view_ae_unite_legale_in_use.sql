/*
View to:
 - switch to the newly imported timestamped table
 - rename to under_score because camelCase breaks DBT
   (even double quoting both .sql and .yml in dbt, it gets ignored and breaks)
 - drop "UniteLegale"  suffix as redundant with view/table names
*/

-- Need to drop as schema has changed
DROP VIEW IF EXISTS {{view_name}} CASCADE;
CREATE VIEW {{view_name}} AS (
    SELECT
        "siren" AS siren,
        "statutDiffusionUniteLegale" AS statut_diffusion,
        "unitePurgeeUniteLegale" AS unite_purgee,
        "dateCreationUniteLegale" AS date_creation,
        "sigleUniteLegale" AS sigle,
        "sexeUniteLegale" AS sexe,
        "prenom1UniteLegale" AS prenom1,
        "prenom2UniteLegale" AS prenom2,
        "prenom3UniteLegale" AS prenom3,
        "prenom4UniteLegale" AS prenom4,
        "prenomUsuelUniteLegale" AS prenom_usuel,
        "pseudonymeUniteLegale" AS pseudonyme,
        "identifiantAssociationUniteLegale" AS identifiant_association,
        "trancheEffectifsUniteLegale" AS tranche_effectifs,
        "anneeEffectifsUniteLegale" AS annee_effectifs,
        "dateDernierTraitementUniteLegale" AS date_dernier_traitement,
        "nombrePeriodesUniteLegale" AS nombre_periodes,
        "categorieEntreprise" AS categorie_entreprise,
        "anneeCategorieEntreprise" AS annee_categorie_entreprise,
        "dateDebut" AS date_debut,
        "etatAdministratifUniteLegale" AS etat_administratif,
        "nomUniteLegale" AS nom,
        "nomUsageUniteLegale" AS nom_usage,
        "denominationUniteLegale" AS denomination,
        "denominationUsuelle1UniteLegale" AS denomination_usuelle_1,
        "denominationUsuelle2UniteLegale" AS denomination_usuelle_2,
        "denominationUsuelle3UniteLegale" AS denomination_usuelle_3,
        "categorieJuridiqueUniteLegale" AS categorie_juridique,
        "activitePrincipaleUniteLegale" AS activite_principale,
        "nomenclatureActivitePrincipaleUniteLegale" AS nomenclature_activite_principale,
        "nicSiegeUniteLegale" AS nic_siege,
        "economieSocialeSolidaireUniteLegale" AS economie_sociale_solidaire,
        "societeMissionUniteLegale" AS societe_mission,
        "caractereEmployeurUniteLegale" AS caractere_employeur,
        "activitePrincipaleNAF25UniteLegale" AS activite_principale_naf_25
    FROM {{table_name}}
)
