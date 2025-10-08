SELECT
    ROW_NUMBER() OVER (ORDER BY acteur_id, source_id) AS id,
    acteur_id AS vueacteur_id,
    source_id
FROM {{ ref('marts_exhaustive_acteur_sources') }}
GROUP BY acteur_id, source_id