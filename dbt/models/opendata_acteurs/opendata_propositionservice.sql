SELECT
    MIN(ps.id) AS id,
    ps.acteur_id,
    ps.action_id
FROM {{ ref('temp_opendata_propositionservice') }} AS ps
INNER JOIN {{ ref('opendata_propositionservice_sous_categories') }} AS pssscat
   ON ps.id = pssscat.propositionservice_id
GROUP BY acteur_id, action_id
