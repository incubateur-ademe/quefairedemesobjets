{{
    config(
        materialized='incremental',
        unique_key='date_snapshot',
        incremental_strategy='delete+insert',
        tags=['exposure', 'stats', 'acteurs', 'visible', 'siret']
    )
}}

SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nombre_acteurs_visible_with_siret
FROM {{ ref('int_acteur_with_siret') }}
