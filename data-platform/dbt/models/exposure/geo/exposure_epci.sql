SELECT
  id,
  code_epci as code,
  nom_epci as nom
FROM {{ ref('int_epci') }}
