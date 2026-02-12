/*
post_hook = partial indexes on high-cardinality columns only for NOT NULL
so we can still speed up the JOINS/FILTERS
*/
{{
  config(
    materialized = 'table',
    tags=['intermediate', 'laposte', 'koumoul_epci', 'cp', 'ville'],
  )
}}


SELECT
    laposte.code_postal AS base_code_postal,
    CASE
        WHEN koumoul_epci.nom_commune LIKE '%e Arrondissement%'
        THEN koumoul_epci.nom_arrondissement
        ELSE koumoul_epci.nom_commune
    END AS base_ville
FROM {{ source('clone', 'clone_koumoul_epci_in_use') }} AS koumoul_epci
INNER JOIN {{ source('clone', 'clone_laposte_code_postal_in_use') }} AS laposte ON laposte.code_commune_insee = koumoul_epci.code_commune
GROUP BY base_code_postal, base_ville
