{{
  config(
    materialized = 'view',
    tags=['base', 'ban', 'lieux_dits'],
  )
}}

SELECT * FROM {{ source('ban', 'clone_ban_lieux_dits_in_use') }}