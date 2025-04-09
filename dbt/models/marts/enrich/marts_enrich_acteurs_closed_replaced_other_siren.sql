{{
  config(
    materialized = 'table',
    tags=['marts', 'enrich', 'closed', 'ae', 'annuaire_entreprises', 'etablissement'],
  )
}}

SELECT * FROM {{ ref('marts_enrich_acteurs_closed_replaced') }}
WHERE remplacer_cohorte = 'siret_dun_autre_siren'
