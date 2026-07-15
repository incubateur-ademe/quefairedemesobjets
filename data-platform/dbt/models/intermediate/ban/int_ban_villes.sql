SELECT
    CASE
      WHEN nom_ancienne_commune = nom_commune THEN NULL
      ELSE nom_ancienne_commune
    END AS ville_ancienne,
    nom_commune AS ville,
    code_postal,
    LEFT(code_postal, 2) AS code_departement
FROM {{ ref('base_ban_adresses') }}
WHERE code_postal IS NOT NULL AND code_postal != ''
GROUP BY 1,2,3,4
