/*
Notes:
 - 🛑 Excluding columns we don't use
 - 👁️‍🗨️ We need to materialize the table to have indexes on siren
      because we already use vues in the request
*/

SELECT

-- Codes
siren,
activite_principale,

-- Status
etat_administratif,

-- Business names
denomination,

-- Director's names
prenom1,
prenom2,
prenom3,
prenom4,
prenom_usuel,
pseudonyme,
nom,
nom_usage

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
