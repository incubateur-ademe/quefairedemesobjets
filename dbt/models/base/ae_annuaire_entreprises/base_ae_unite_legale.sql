/*
Notes:
 - 🛑 Excluding columns we don't use
 - 🧹 Converting '[ND]' (non-diffusile) to NULL to make
      our data lighter and easier to work with
 - 👁️‍🗨️ We need to materialize the table to have indexes on siren
      because we already use vues in the request
*/

SELECT

-- Codes
{{ target.schema }}.udf_ae_string_cleanup(siren) AS siren,
{{ target.schema }}.udf_ae_string_cleanup(activite_principale) AS activite_principale,

-- Status
{{ target.schema }}.udf_ae_string_cleanup(etat_administratif) AS etat_administratif,

-- Business names
{{ target.schema }}.udf_ae_string_cleanup(denomination) AS denomination,

-- Director's names
{{ target.schema }}.udf_ae_string_cleanup(prenom1) AS prenom1,
{{ target.schema }}.udf_ae_string_cleanup(prenom2) AS prenom2,
{{ target.schema }}.udf_ae_string_cleanup(prenom3) AS prenom3,
{{ target.schema }}.udf_ae_string_cleanup(prenom4) AS prenom4,
{{ target.schema }}.udf_ae_string_cleanup(prenom_usuel) AS prenom_usuel,
{{ target.schema }}.udf_ae_string_cleanup(pseudonyme) AS pseudonyme,
{{ target.schema }}.udf_ae_string_cleanup(nom) AS nom,
{{ target.schema }}.udf_ae_string_cleanup(nom_usage) AS nom_usage

FROM {{ source('ae', 'clone_ae_unite_legale_in_use') }}
/* We can't do random sampling else we risk having
no matching etablissement vs. unite legale. Can't
sample on location as not available in unite to match,
falling back to latest SIRET/SIREN as they will give
matches while representing recent data.
*/
{% if env_var('DBT_SAMPLING', 'false') == 'true' %}
ORDER BY siren DESC
LIMIT 500000
{% endif %}