/*
Notes:
 - 🌍 Filtering out non-FR establishments
 - 🛑 Excluding columns we don't use
 - 👁️‍🗨️ AE tables large (10Ms' rows) so only int layer as table
*/
{{
  config(
    materialized = 'view',
    tags=['base', 'ae', 'annuaire_entreprises', 'etablissement'],
  )
}}

SELECT

-- Codes
siret,
activite_principale,

-- Status
etat_administratif,

-- Address
numero_voie,
complement_adresse,
type_voie,
libelle_voie,
code_postal,
libelle_commune

FROM {{ source('ae', 'clone_ae_etablissement_in_use') }}
-- Filtering out foreign establishments as our focus is France
-- On 2025-03-17 this allows excluding ~316K rows
WHERE code_pays_etranger IS NULL