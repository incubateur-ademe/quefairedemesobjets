SELECT
    id,
    code_epci AS code,
    nom_epci  AS nom
FROM {{ ref('int_epci') }}
