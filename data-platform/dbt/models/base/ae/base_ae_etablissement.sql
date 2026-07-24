/*
Notes:
 - 🌍 Filtering out non-FR establishments
 - 🛑 Excluding columns we don't use
 - 👁️‍🗨️ We need to materialize the table to have indexes on siren
      because we already use vues in the request
*/

SELECT

-- Codes
siret,
siren,
activite_principale,

-- Names
denomination_usuelle,

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
-- Ignore closed establishments before 2006 (20 years ago)
WHERE NOT (date_debut < '2006-01-01' AND etat_administratif = 'F')

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
