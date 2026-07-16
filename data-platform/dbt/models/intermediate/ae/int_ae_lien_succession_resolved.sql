/*
Resolve transitive succession chains to their final successor.

Given:  x -> b, x -> y, y -> z, z -> a
Result: x -> b, x -> a, y -> a, z -> a

Uses a recursive CTE with cycle detection to handle
potential circular references in the source data.
*/

WITH RECURSIVE base_links AS (
    SELECT
        siret_predecesseur,
        etat_administratif_predecesseur,
        siren_successeur,
        siret_successeur,
        etat_administratif_successeur,
        date_lien_succession,
        transfert_siege,
        continuite_economique
    FROM {{ ref('base_ae_lien_succession') }}
),

succession_chain AS (
    SELECT
        siret_predecesseur,
        etat_administratif_predecesseur,
        siren_successeur,
        siret_successeur,
        etat_administratif_successeur,
        date_lien_succession,
        transfert_siege,
        continuite_economique,
        ARRAY[siret_predecesseur]::varchar[] AS visited,
        1 AS profondeur
    FROM base_links

    UNION ALL

    SELECT
        sc.siret_predecesseur,
        sc.etat_administratif_predecesseur,
        bl.siren_successeur,
        bl.siret_successeur,
        bl.etat_administratif_successeur,
        LEAST(sc.date_lien_succession, bl.date_lien_succession),
        sc.transfert_siege AND bl.transfert_siege,
        sc.continuite_economique AND bl.continuite_economique,
        sc.visited || bl.siret_predecesseur,
        sc.profondeur + 1
    FROM succession_chain sc
    INNER JOIN base_links bl
        ON sc.siret_successeur = bl.siret_predecesseur
    WHERE bl.siret_predecesseur != ALL(sc.visited)
      AND sc.profondeur < 100
)

SELECT
    sc.siret_predecesseur,
    sc.etat_administratif_predecesseur,
    sc.siren_successeur,
    sc.siret_successeur,
    sc.etat_administratif_successeur,
    MAX(sc.date_lien_succession) as date_lien_succession,
    -- if one of the path has transfert_siege = true, then the result is true
    BOOL_OR(sc.transfert_siege) as transfert_siege,
    -- if one of the path has continuite_economique = true, then the result is true
    BOOL_OR(sc.continuite_economique) as continuite_economique,
    -- keep the shortest path
    MIN(sc.profondeur) as profondeur
FROM succession_chain sc
LEFT JOIN base_links bl
    ON sc.siret_successeur = bl.siret_predecesseur
WHERE bl.siret_predecesseur IS NULL
-- Deduplication by siret_predecesseur and siret_successeur
GROUP BY sc.siret_predecesseur, sc.etat_administratif_predecesseur, sc.siren_successeur, sc.siret_successeur, sc.etat_administratif_successeur
ORDER BY sc.siret_predecesseur, profondeur DESC
