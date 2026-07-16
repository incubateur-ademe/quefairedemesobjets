SELECT
  CAST(ROW_NUMBER() OVER (ORDER BY code_epci, nom_epci) AS INTEGER) AS id,
  code_epci AS code,
  nom_epci AS nom
FROM {{ ref('base_koumoul_epci') }}
WHERE code_epci IS NOT NULL
AND nom_epci IS NOT NULL
GROUP BY code_epci, nom_epci
