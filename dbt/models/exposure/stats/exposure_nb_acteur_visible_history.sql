{{
    config(
        materialized='incremental',
        unique_key='date_snapshot',
        incremental_strategy='delete+insert',
        tags=['exposure', 'stats', 'acteurs', 'visible']
    )
}}

SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nombre_acteurs_visible
FROM {{ ref('base_acteur_visible') }}
