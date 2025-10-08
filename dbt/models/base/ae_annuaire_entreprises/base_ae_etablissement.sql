/*
Notes:
 - 🌍 Filtering out non-FR establishments
 - 🛑 Excluding columns we don't use
 - 👁️‍🗨️ We need to materialize the table to have indexes on siren
      because we already use vues in the request
*/

SELECT

-- Codes
{{ target.schema }}.udf_ae_string_cleanup(siret) AS siret,
{{ target.schema }}.udf_ae_string_cleanup(siren) AS siren,
{{ target.schema }}.udf_ae_string_cleanup(activite_principale) AS activite_principale,

-- Names
{{ target.schema }}.udf_ae_string_cleanup(denomination_usuelle) AS denomination_usuelle,

-- Status
{{ target.schema }}.udf_ae_string_cleanup(etat_administratif) AS etat_administratif,

-- Address
{{ target.schema }}.udf_ae_string_cleanup(numero_voie) AS numero_voie,
{{ target.schema }}.udf_ae_string_cleanup(complement_adresse) AS complement_adresse,
{{ target.schema }}.udf_ae_string_cleanup(type_voie) AS type_voie,
{{ target.schema }}.udf_ae_string_cleanup(libelle_voie) AS libelle_voie,
{{ target.schema }}.udf_ae_string_cleanup(code_postal) AS code_postal,
{{ target.schema }}.udf_ae_string_cleanup(libelle_commune) AS libelle_commune

FROM {{ source('ae', 'clone_ae_etablissement_in_use') }}
-- Filtering out foreign establishments as our focus is France
-- On 2025-03-17 this allows excluding ~316K rows
WHERE code_pays_etranger IS NULL
-- Ignore closed establishments before 2006 (20 years ago)
AND NOT (date_debut < '2006-01-01' AND etat_administratif = 'F')

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