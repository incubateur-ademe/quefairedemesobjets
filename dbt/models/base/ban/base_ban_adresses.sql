{{
  config(
    materialized = 'view',
    tags=['base', 'ban', 'adresses'],
  )
}}
-- Large source: only reading what's needed
SELECT
    /* Creating complete adresse to do lookups
    and compare vs. ours rep = ex: "bis" */
    udf_columns_concat_unique_non_empty(numero,rep,nom_voie) AS adresse,
    /* Also keeping separate column for numero
    as it's a common suggestion filter */
    numero AS adresse_numero,
    nom_commune AS ville,
    nom_ancienne_commune AS ville_ancienne,
    code_postal,
    LEFT(code_postal, 2) AS code_departement,
    lat as latitude,
    lon as longitude
FROM {{ source('ban', 'clone_ban_adresses_in_use') }}
WHERE code_postal NOT IN ('',NULL)
ORDER BY code_postal ASC