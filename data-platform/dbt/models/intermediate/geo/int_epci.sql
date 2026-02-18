SELECT
  CAST(ROW_NUMBER() OVER (ORDER BY epci.code_epci, epci.nom_epci) AS INTEGER) AS id,
  epci.code_epci,
  epci.nom_epci
FROM {{ source('clone','clone_koumoul_epci_in_use') }} AS epci
WHERE epci.code_epci IS NOT NULL
AND epci.nom_epci IS NOT NULL
GROUP BY epci.code_epci, epci.nom_epci
