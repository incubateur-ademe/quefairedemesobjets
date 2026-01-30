{{
    config(
        materialized='incremental',
        unique_key='date_snapshot',
        incremental_strategy='delete+insert',
        tags=['exposure', 'stats', 'acteurs', 'visible', 'siret', 'actif']
    )
}}

SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nb_acteur_visible_with_siret_actif
FROM {{ ref('marts_acteur_siret_actif') }}
