WITH
  sampled AS (
    SELECT
      identifiant_unique,
      parent_id,
      est_parent,
      source_id,
      "location",
      code_postal,
      acteur_type_id,
      row_number() OVER (
        ORDER BY
          MD5(identifiant_unique::TEXT || '42')
      ) AS rn -- Seed pour le reproductibilité
    FROM
      qfdmo_vueacteur qv
    WHERE
      qv.statut <> 'SUPPRIME'
  ),
  sampled_filtered AS (
    SELECT
      *
    FROM
      sampled
    WHERE
      rn <= 100000 -- Permet la création d'environ 50k paires
  ),
  randomized_pairs AS (
    SELECT
      identifiant_unique,
      parent_id,
      est_parent,
      source_id,
      "location",
      code_postal,
      acteur_type_id,
      row_number() OVER (
        ORDER BY
          MD5(identifiant_unique::TEXT || '42')
      ) AS rn -- Mélange aléatoire REPRODUCTIBLE de l'échantillon
    FROM
      sampled_filtered
  )
  -- Création des paires
SELECT
  MIN(a.identifiant_unique) AS identifiant_unique_i,
  MAX(b.identifiant_unique) AS identifiant_unique_j
FROM
  randomized_pairs a
  JOIN randomized_pairs b ON FLOOR((a.rn - 1) / 2) = FLOOR((b.rn - 1) / 2) -- Groupe en paire en utilisant le ~row_number/2 comme clé
  AND a.identifiant_unique < b.identifiant_unique -- S'assure de ne pas avoir de paires avec les mêmes ids dans un ordre différent
  AND a.identifiant_unique <> coalesce(b.parent_id, '') -- acteur_j n'est pas un parent de acteur_i
  AND b.identifiant_unique <> coalesce(a.parent_id, '') -- acteur_i n'est pas un parent de acteur_j
  and not a.est_parent and not b.est_parent -- On exclue les parent_ids des paires
  AND coalesce(a.parent_id, 'N/A') != coalesce(b.parent_id, 'N/A2') -- les deux acteurs n'ont pas le même parent
  AND coalesce(a.source_id, -1) != coalesce(b.source_id, -2) -- les deux acteurs n'ont pas la même source
  AND coalesce(a.acteur_type_id, -1) != coalesce(b.acteur_type_id, -2) -- les deux acteurs ne sont pas du même type
  AND a.acteur_type_id!=10 AND b.acteur_type_id!=10 -- Exclusion des PAV publics
  AND (
    ST_DistanceSpheroid (a."location"::geometry, b."location"::geometry) >= 10000
    OR left(a.code_postal, 2) != left(b.code_postal, 2)
  ) -- plus de 10km entre les deux ou département différent
GROUP BY
  FLOOR((a.rn - 1) / 2)