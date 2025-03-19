/*
Notes:
 - 🖊️ Renaming columns to follow our naming convention
 - 🧱 Only layer materialized as table (subsequent layers, because
  they JOIN with continuously changing QFDMO data are kept as views)
*/
{{
  config(
    materialized = 'table',
    tags=['intermediate', 'ae', 'annuaire_entreprises', 'etablissement'],
    indexes=[
      {'columns': ['siret'], 'unique': True},
      {'columns': ['est_actif']},
    ]
  )
}}

SELECT
    -- Codes
    siret,
    activite_principale AS naf, -- Making NAF explicit since it's a code

    /*
    Is active or not: converting this field to BOOLEAN to:
     - have a consistent/clear way to know what's active
       across unite_legale and etablissement despite them
       using different flags
     - create more efficient data type and index
    */
    CASE etat_administratif
      WHEN 'A' THEN TRUE
      ELSE FALSE
    END AS est_actif,

    -- Addresse
    udf_columns_concat_unique_non_empty(
      numero_voie,
      type_voie,
      libelle_voie
    ) AS adresse,
    complement_adresse AS adresse_complement,
    code_postal,
    libelle_commune AS ville

FROM {{ ref('base_ae_etablissement') }}