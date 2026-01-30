{{
    config(
        materialized='incremental',
        unique_key='date_snapshot',
        incremental_strategy='delete+insert',
        tags=['exposure', 'stats', 'acteurs', 'stacked']
    )
}}

SELECT
    CURRENT_DATE AS date_snapshot,
    COUNT(*) AS nombre_acteurs_stacked
FROM {{ ref('marts_acteur_stacked') }}
