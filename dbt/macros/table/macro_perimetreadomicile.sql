{%- macro perimetreadomicile(ephemeral_filtered_acteur) -%}


with parent_perimetreadomicile AS (
    SELECT
        pad.id AS id,
        tcfa.parent_id AS acteur_id, -- all pad for parent
        pad.type AS type,
        pad.valeur AS valeur
    FROM {{ ref('int_perimetreadomicile') }} AS pad
        INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS tcfa
            ON pad.acteur_id = tcfa.identifiant_unique
                AND tcfa.parent_id IS NOT NULL
),
nochild_perimetreadomicile AS (
    SELECT
    pad.id AS id,
    pad.acteur_id AS acteur_id,
    pad.type AS type,
    pad.valeur AS valeur
    FROM {{ ref('int_perimetreadomicile') }} AS pad
    INNER JOIN {{ ref(ephemeral_filtered_acteur) }} AS cfa
        ON pad.acteur_id = cfa.identifiant_unique AND cfa.parent_id is null
)

SELECT * FROM parent_perimetreadomicile
union all
SELECT * FROM nochild_perimetreadomicile

{%- endmacro -%}