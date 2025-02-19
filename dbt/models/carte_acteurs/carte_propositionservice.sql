SELECT
    MIN(ps.id) AS id,
    ps.acteur_id,
    ps.action_id
FROM {{ ref('temp_propositionservice') }} AS ps
INNER JOIN {{ ref('carte_propositionservice_sous_categories') }} AS pssscat
   ON ps.id = pssscat.propositionservice_id
GROUP BY acteur_id, action_id
