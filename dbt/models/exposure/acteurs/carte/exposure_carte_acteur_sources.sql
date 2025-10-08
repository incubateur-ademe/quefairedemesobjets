SELECT
    ROW_NUMBER() OVER (ORDER BY acteur_id, source_id) AS id,
    acteur_id AS displayedacteur_id,
    source_id
 FROM {{ ref('marts_carte_acteur_sources') }}
 GROUP BY acteur_id, source_id
