/*
Notes:
 - 🧹 Converting '[ND]' (non-diffusible) to NULL to make
      our data lighter and easier to work with
 - 🖊️ Renaming columns to follow our naming convention
    🟠 in particular "nom" referring to business and not person
 - 🧱 Only layer materialized as table (subsequent layers, because
  they JOIN with continuously changing QFDMO data are kept as views)
*/

WITH cleaned AS (
    SELECT
        {{ target.schema }}.udf_ae_string_cleanup(siren) AS siren,
        {{ target.schema }}.udf_ae_string_cleanup(activite_principale) AS activite_principale,
        {{ target.schema }}.udf_ae_string_cleanup(etat_administratif) AS etat_administratif,
        {{ target.schema }}.udf_ae_string_cleanup(denomination) AS denomination,
        {{ target.schema }}.udf_ae_string_cleanup(prenom1) AS prenom1,
        {{ target.schema }}.udf_ae_string_cleanup(prenom2) AS prenom2,
        {{ target.schema }}.udf_ae_string_cleanup(prenom3) AS prenom3,
        {{ target.schema }}.udf_ae_string_cleanup(prenom4) AS prenom4,
        {{ target.schema }}.udf_ae_string_cleanup(prenom_usuel) AS prenom_usuel,
        {{ target.schema }}.udf_ae_string_cleanup(pseudonyme) AS pseudonyme,
        {{ target.schema }}.udf_ae_string_cleanup(nom) AS nom,
        {{ target.schema }}.udf_ae_string_cleanup(nom_usage) AS nom_usage
    FROM {{ ref('base_ae_unite_legale') }}
)

SELECT
    -- Codes
    siren,
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

    -- In QFDMO, "nom" refers to the business name
    -- we use "nom_commercial" to avoid collision
    -- with the original "nom" referring to directors
    denomination AS nom_commercial,

    /*
    Director's first names and last names for the sake
    of GDPR lookups, trying our best to pre-filter with SQL:
     - normalize to increase chances of matching
     - keep each column separate for a potential substring match
    */
    nom AS dirigeant_nom,
    nom_usage AS dirigeant_nom_usage,
    pseudonyme AS dirigeant_pseudonyme,
    prenom1 AS dirigeant_prenom1,
    prenom2 AS dirigeant_prenom2,
    prenom3 AS dirigeant_prenom3,
    prenom4 AS dirigeant_prenom4,
    prenom_usuel AS dirigeant_prenom_usuel,
    -- TRUE if ANY names NOT NULL for more efficient pre-filtering
    COALESCE(
      nom,
      nom_usage,
      pseudonyme,
      prenom1,
      prenom2,
      prenom3,
      prenom4,
      prenom_usuel
    ) IS NOT NULL AS a_dirigeant_noms_ou_prenoms_non_null

FROM cleaned
