SELECT identifiant_unique, siren, siret, code_postal, ville
FROM {{ ref('int_acteur_with_siren') }}
WHERE siret = ''
