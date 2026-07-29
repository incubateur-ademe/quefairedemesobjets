WITH enfants AS (
    SELECT DISTINCT
        (parent_id)                   AS parent_id,
        jsonb_agg(identifiant_unique) AS enfants
    FROM {{ ref('base_revisionacteur') }}
    GROUP BY parent_id
)

SELECT
    a.*,
    epci.id                                                      AS epci_id,
    cast(st_x(cast(a.location AS geometry)) AS double precision) AS latitude,
    -- TODO : add lat and long, issue intrpreting double precision by dbt
    cast(st_y(cast(a.location AS geometry)) AS double precision) AS longitude,
    e.enfants
        AS liste_enfants,
    coalesce(cae.code_commune_insee, '')
        AS code_commune_insee,
    e.enfants IS NOT NULL                                        AS est_parent,
    jsonb_array_length(e.enfants)
        AS nombre_enfants,
    ca.identifiant_unique IS NOT NULL
        AS est_dans_carte,
    oa.identifiant_unique IS NOT NULL
        AS est_dans_opendata
FROM {{ ref('int_acteur') }} AS a
LEFT JOIN enfants AS e
    ON a.identifiant_unique = e.parent_id
LEFT JOIN {{ ref('marts_carte_acteur') }} AS ca
    ON a.identifiant_unique = ca.identifiant_unique
LEFT JOIN {{ ref('marts_opendata_acteur') }} AS oa
    ON a.identifiant_unique = oa.identifiant_unique
LEFT JOIN {{ ref('marts_exhaustive_acteur_epci') }} AS cae
    ON a.identifiant_unique = cae.identifiant_unique
LEFT JOIN {{ ref('base_epci') }} AS epci
    ON cae.code_epci = epci.code
