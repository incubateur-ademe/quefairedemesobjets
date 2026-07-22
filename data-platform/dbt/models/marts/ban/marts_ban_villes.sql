SELECT
    ville_ancienne,
    ville,
    code_postal,
    code_departement
FROM {{ ref('int_ban_adresses') }}
GROUP BY 1, 2, 3, 4
