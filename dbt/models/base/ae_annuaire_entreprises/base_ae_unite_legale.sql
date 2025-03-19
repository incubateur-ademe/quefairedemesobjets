/*
Notes:
 - 🛑 Excluding columns we don't use
 - 🧹 Converting '[ND]' (non-diffusile) to NULL to make
      our data lighter and easier to work with
 - 👁️‍🗨️ AE tables large (10Ms' rows) so only int layer as table
*/
{{
  config(
    materialized = 'view',
    tags=['intermediate', 'ae', 'annuaire_entreprises', 'unite_legale'],
  )
}}

SELECT

-- Codes
siren,
activite_principale,

-- Status
etat_administratif,

-- Business names
denomination,

-- Director's names
CASE WHEN prenom1 = '[ND]' THEN NULL ELSE prenom1 END AS prenom1,
CASE WHEN prenom2 = '[ND]' THEN NULL ELSE prenom2 END AS prenom2,
CASE WHEN prenom3 = '[ND]' THEN NULL ELSE prenom3 END AS prenom3,
CASE WHEN prenom4 = '[ND]' THEN NULL ELSE prenom4 END AS prenom4,
CASE WHEN prenom_usuel = '[ND]' THEN NULL ELSE prenom_usuel END AS prenom_usuel,
CASE WHEN pseudonyme = '[ND]' THEN NULL ELSE pseudonyme END AS pseudonyme,
CASE WHEN nom = '[ND]' THEN NULL ELSE nom END AS nom,
CASE WHEN nom_usage = '[ND]' THEN NULL ELSE nom_usage END AS nom_usage

FROM {{ source('ae', 'clone_ae_unite_legale_in_use') }}