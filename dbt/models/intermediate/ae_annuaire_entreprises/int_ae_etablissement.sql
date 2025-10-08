/*
Notes:
 - 🖊️ Renaming columns to follow our naming convention
 - 🧱 We force tu use indexes `Merge Join` instead of `Hash Join`
      to improve performance because siren has a high cardinality
*/

SELECT
    -- Codes
    etab.siret,
    etab.activite_principale AS naf, -- Making NAF explicit being a well-known code

    -- Names
    CASE
      WHEN etab.denomination_usuelle IS NOT NULL THEN etab.denomination_usuelle
      WHEN etab.denomination_usuelle IS NULL AND unite.denomination IS NOT NULL THEN unite.denomination
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
    {{ target.schema }}.udf_columns_concat_unique_non_empty(
      etab.numero_voie,
      etab.type_voie,
      etab.libelle_voie
    ) AS adresse,
    etab.numero_voie AS adresse_numero,
    etab.complement_adresse AS adresse_complement,
    etab.code_postal,
    etab.libelle_commune AS ville,
    {{ target.schema }}.udf_normalize_string_for_match(
      {{ target.schema }}.udf_columns_concat_unique_non_empty(
        etab.numero_voie,
        etab.type_voie,
        etab.libelle_voie
      )
    ) AS adresse_normalize_string_for_match

FROM {{ ref('base_ae_etablissement') }} AS etab
/* Joining with unite_legale to bring some essential
data from parent unite into each etablissement (saves
us from making expensive JOINS in downstream models) */
JOIN {{ ref('base_ae_unite_legale') }} AS unite
ON unite.siren = etab.siren
/* Here we keep unavailable names as int_ models aren't
responsible for business logic. Keeping allows investigating
AND nom != {{ value_unavailable() }}
*/
