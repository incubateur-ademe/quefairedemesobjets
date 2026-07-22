SELECT * FROM {{ source('ban', 'clone_ban_adresses_in_use') }}
