/*
post_hook = partial indexes on high-cardinality columns only for NOT NULL
so we can still speed up the JOINS/FILTERS
*/
{{
  config(
    materialized = 'table',
    tags=['intermediate', 'ban', 'adresses'],
    indexes=[
      {'columns': ['code_postal']},
      {'columns': ['code_departement']},
    ],
    post_hook=[
      "CREATE INDEX ON {{ this }}(ville_ancienne) WHERE ville_ancienne IS NOT NULL",
      "CREATE INDEX ON {{ this }}(adresse_numero) WHERE adresse_numero IS NOT NULL",
    ]
  )
}}


SELECT *
FROM {{ ref('base_ban_adresses') }}