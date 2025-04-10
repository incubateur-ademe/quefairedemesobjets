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
udf_ae_string_cleanup(siret) AS siret,
udf_ae_string_cleanup(activite_principale) AS activite_principale,

-- Names
udf_ae_string_cleanup(denomination_usuelle) AS denomination_usuelle,

-- Status
udf_ae_string_cleanup(etat_administratif) AS etat_administratif,

-- Address
udf_ae_string_cleanup(numero_voie) AS numero_voie,
udf_ae_string_cleanup(complement_adresse) AS complement_adresse,
udf_ae_string_cleanup(type_voie) AS type_voie,
udf_ae_string_cleanup(libelle_voie) AS libelle_voie,
udf_ae_string_cleanup(code_postal) AS code_postal,
udf_ae_string_cleanup(libelle_commune) AS libelle_commune

FROM {{ source('ae', 'clone_ae_etablissement_in_use') }}
-- Filtering out foreign establishments as our focus is France
-- On 2025-03-17 this allows excluding ~316K rows
WHERE code_pays_etranger IS NULL
{% if env_var('DBT_SAMPLING', 'false') == 'true' %}
/* We can't do random sampling else we risk having
no matching etablissement vs. unite legale. Can't
sample on location as not available in unite to match,
falling back to latest SIRET/SIREN as they will give
matches while representing recent data.
*/
/* TODO: improve sampling by grabbing what we have
in acteurs + a little more if we can suggestion models
to have more data */
ORDER BY siret DESC
LIMIT 1000000
{% endif %}
