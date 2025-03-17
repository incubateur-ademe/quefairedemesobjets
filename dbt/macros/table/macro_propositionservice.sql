{%- macro propositionservice(ephemeral_filtered_propositionservice, propositionservice_sous_categories ) -%}

SELECT
    ps.id,
    ps.acteur_id,
    ps.action_id
FROM {{ ref(ephemeral_filtered_propositionservice) }} AS ps
INNER JOIN {{ ref(propositionservice_sous_categories) }} AS pssscat
   ON ps.id = pssscat.propositionservice_id
GROUP BY ps.id, ps.acteur_id, ps.action_id

{%- endmacro -%}
