WITH acteurs AS (
    SELECT
        identifiant_unique,
        siren,
        code_postal
    FROM {{ ref('int_acteur_with_siren_without_siret') }}
),

active_etablissements AS (
    SELECT ae.siren, ae.siret, ae.code_postal
    FROM {{ ref('int_ae_etablissement') }} AS ae
    INNER JOIN {{ ref('int_acteur_with_siren_without_siret') }} AS av
        ON ae.siren = av.siren
    WHERE ae.etat_administratif = 'A'
    GROUP BY ae.siren, ae.siret, ae.code_postal
),

-- Un seul SIRET actif pour le SIREN, quel que soit le code postal
siren_unique_siret AS (
    SELECT
        siren,
        MAX(siret) AS siret
    FROM active_etablissements
    GROUP BY siren
    HAVING COUNT(DISTINCT siret) = 1
),

-- Sinon : un seul SIRET actif pour le couple SIREN + code postal de l'acteur
code_postal_unique_siret AS (
    SELECT
        av.identifiant_unique,
        av.siren,
        MAX(ae.siret) AS siret
    FROM acteurs AS av
    INNER JOIN active_etablissements AS ae
        ON
            av.siren = ae.siren
            AND av.code_postal = ae.code_postal
    GROUP BY av.identifiant_unique, av.siren
    HAVING COUNT(DISTINCT ae.siret) = 1
)

SELECT
    av.identifiant_unique,
    av.siren,
    av.code_postal,
    COALESCE(sus.siret, cpus.siret) AS siret
FROM acteurs AS av
LEFT JOIN siren_unique_siret AS sus
    ON av.siren = sus.siren
LEFT JOIN code_postal_unique_siret AS cpus
    ON av.identifiant_unique = cpus.identifiant_unique
WHERE COALESCE(sus.siret, cpus.siret) IS NOT NULL
