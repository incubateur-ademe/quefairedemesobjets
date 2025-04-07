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
    etab.siret,
    etab.activite_principale AS naf, -- Making NAF explicit being a well-known code

    -- Names
    CASE
      WHEN TRIM(etab.denomination_usuelle) NOT IN ('', '[ND]', NULL) THEN TRIM(etab.denomination_usuelle)
      WHEN TRIM(etab.denomination_usuelle) IN ('', '[ND]', NULL) AND TRIM(unite.denomination) NOT IN ('', '[ND]', NULL) THEN TRIM(unite.denomination)
      ELSE {{ value_unavailable() }}
    END AS nom,

    /*
    Is active or not: converting this field to BOOLEAN to:
     - have a consistent/clear way to know what's active
       across unite_legale and etablissement despite them
       using different flags
     - create more efficient data type and index
    */
    CASE etab.etat_administratif
      WHEN 'A' THEN TRUE
      ELSE FALSE
    END AS est_actif,
    CASE unite.etat_administratif
      WHEN 'A' THEN TRUE
      ELSE FALSE
    END AS unite_est_actif,

    -- Addresse
    udf_columns_concat_unique_non_empty(
      etab.numero_voie,
      etab.type_voie,
      etab.libelle_voie
    ) AS adresse,
    etab.complement_adresse AS adresse_complement,
    etab.code_postal,
    etab.libelle_commune AS ville

FROM {{ ref('base_ae_etablissement') }} AS etab
/* Joining with unite_legale to bring some essential
data from parent unite into each etablissement to save
us from making expensive JOINS in downstream models */
JOIN {{ ref('base_ae_unite_legale') }} AS unite
ON unite.siren = LEFT(etab.siret,9)
/* Here we keep unavailable names as int_ models aren't
responsible for business logic. Keeping allows investigating
AND nom != {{ value_unavailable() }}
*/