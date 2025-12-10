WITH enfants AS (
    select
        distinct(parent_id) as parent_id,
        jsonb_agg(identifiant_unique) as enfants
    from {{ ref('base_revisionacteur') }}
    group by parent_id
)

select a.*,
    COALESCE(cae.code_commune_insee, '') as code_commune_insee,
    epci.id as epci_id,
    -- TODO : add lat and long, issue interpreting double precision by dbt
    CAST(ST_X(a.location::geometry) AS DOUBLE PRECISION) AS latitude,
    CAST(ST_Y(a.location::geometry) AS DOUBLE PRECISION) AS longitude,
    e.enfants IS NOT NULL AS est_parent,
    e.enfants AS liste_enfants,
    jsonb_array_length(e.enfants) AS nombre_enfants,
    ca.identifiant_unique IS NOT NULL AS est_dans_carte,
    oa.identifiant_unique IS NOT NULL AS est_dans_opendata
from {{ ref('int_acteur') }} as a
LEFT JOIN enfants AS e
  ON a.identifiant_unique = e.parent_id
LEFT JOIN {{ ref('marts_carte_acteur') }} AS ca
  ON a.identifiant_unique = ca.identifiant_unique
LEFT JOIN {{ ref('marts_opendata_acteur') }} AS oa
  ON a.identifiant_unique = oa.identifiant_unique
LEFT JOIN {{ ref('marts_exhaustive_acteur_epci') }} AS cae
  ON a.identifiant_unique = cae.identifiant_unique
LEFT JOIN {{ source('qfdmo','qfdmo_epci') }} AS epci
  ON cae.code_epci = epci.code
