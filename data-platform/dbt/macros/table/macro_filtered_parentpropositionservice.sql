{%- macro filtered_parentpropositionservice(ephemeral_filtered_acteur ) -%}

SELECT
    tvps.id AS id,
    tcfa.parent_id AS parent_id,
    tvps.acteur_id AS acteur_id,
    tvps.action_id AS action_id
FROM {{ ref('int_propositionservice') }} AS tvps
    INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS tcfa
        ON tvps.acteur_id = tcfa.identifiant_unique
            AND tcfa.parent_id IS NOT NULL

{%- endmacro -%}