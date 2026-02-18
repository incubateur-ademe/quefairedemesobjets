/*
post_hook = partial indexes on high-cardinality columns only for NOT NULL
so we can still speed up the JOINS/FILTERS
*/
{{
  config(
    materialized = 'table',
    tags=['intermediate', 'ban', 'villes'],
    indexes=[
      {'columns': ['ville_ancienne']},
      {'columns': ['ville']},
      {'columns': ['code_postal']},
      {'columns': ['code_departement']},
    ],
    post_hook=[
      "CREATE INDEX ON {{ this }}(ville_ancienne) WHERE ville_ancienne IS NOT NULL",
    ]
  )
}}


SELECT
    ville_ancienne,
    ville,
    code_postal,
    code_departement
FROM {{ ref('base_ban_adresses') }}
GROUP BY 1,2,3,4