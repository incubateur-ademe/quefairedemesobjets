/*
View to:
 - switch to the newly imported timestamped table
 - rename to under_score because camelCase breaks DBT
   (even double quoting both .sql and .yml in dbt, it gets ignored and breaks)
 - drop "Etablissement" suffix as redundant with view/table names
*/

-- Need to drop as schema has changed
DROP VIEW IF EXISTS {{view_name}} CASCADE;
CREATE VIEW {{view_name}} AS (
    SELECT
        "siren" AS siren,
        "nic" AS nic,
        "siret" AS siret,
        "statutDiffusionEtablissement" AS statut_diffusion,
        "dateCreationEtablissement" AS date_creation,
        "trancheEffectifsEtablissement" AS tranche_effectifs,
        "anneeEffectifsEtablissement" AS annee_effectifs,
        "activitePrincipaleRegistreMetiersEtablissement" AS activite_principale_registre_metiers,
        "dateDernierTraitementEtablissement" AS date_dernier_traitement,
        "etablissementSiege" AS etablissement_siege,
        "nombrePeriodesEtablissement" AS nombre_periodes,
        "complementAdresseEtablissement" AS complement_adresse,
        "numeroVoieEtablissement" AS numero_voie,
        "indiceRepetitionEtablissement" AS indice_repetition,
        "dernierNumeroVoieEtablissement" AS dernier_numero_voie,
        "indiceRepetitionDernierNumeroVoieEtablissement" AS indice_repetition_dernier_numero_voie,
        "typeVoieEtablissement" AS type_voie,
        "libelleVoieEtablissement" AS libelle_voie,
        "codePostalEtablissement" AS code_postal,
        "libelleCommuneEtablissement" AS libelle_commune,
        "libelleCommuneEtrangerEtablissement" AS libelle_commune_etranger,
        "distributionSpecialeEtablissement" AS distribution_speciale,
        "codeCommuneEtablissement" AS code_commune,
        "codeCedexEtablissement" AS code_cedex,
        "libelleCedexEtablissement" AS libelle_cedex,
        "codePaysEtrangerEtablissement" AS code_pays_etranger,
        "libellePaysEtrangerEtablissement" AS libelle_pays_etranger,
        "identifiantAdresseEtablissement" AS identifiant_adresse,
        "coordonneeLambertAbscisseEtablissement" AS coordonnee_lambert_abscisse,
        "coordonneeLambertOrdonneeEtablissement" AS coordonnee_lambert_ordonnee,
        "complementAdresse2Etablissement" AS complement_adresse2,
        "numeroVoie2Etablissement" AS numero_voie2,
        "indiceRepetition2Etablissement" AS indice_repetition2,
        "typeVoie2Etablissement" AS type_voie2,
        "libelleVoie2Etablissement" AS libelle_voie2,
        "codePostal2Etablissement" AS code_postal2,
        "libelleCommune2Etablissement" AS libelle_commune2,
        "libelleCommuneEtranger2Etablissement" AS libelle_commune_etranger2,
        "distributionSpeciale2Etablissement" AS distribution_speciale2,
        "codeCommune2Etablissement" AS code_commune2,
        "codeCedex2Etablissement" AS code_cedex2,
        "libelleCedex2Etablissement" AS libelle_cedex2,
        "codePaysEtranger2Etablissement" AS code_pays_etranger2,
        "libellePaysEtranger2Etablissement" AS libelle_pays_etranger2,
        "dateDebut" AS date_debut,
        "etatAdministratifEtablissement" AS etat_administratif,
        "enseigne1Etablissement" AS enseigne1,
        "enseigne2Etablissement" AS enseigne2,
        "enseigne3Etablissement" AS enseigne3,
        "denominationUsuelleEtablissement" AS denomination_usuelle,
        "activitePrincipaleEtablissement" AS activite_principale,
        "nomenclatureActivitePrincipaleEtablissement" AS nomenclature_activite_principale,
        "caractereEmployeurEtablissement" AS caractere_employeur,
        "activitePrincipaleNAF25UniteLegale" AS activite_principale_naf_25
    FROM {{table_name}}
)
