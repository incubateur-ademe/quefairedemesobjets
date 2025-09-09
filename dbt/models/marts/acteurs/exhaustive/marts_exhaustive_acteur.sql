WITH enfants AS (
    select
        distinct(parent_id) as parent_id,
        jsonb_agg(identifiant_unique) as enfants
    from {{ ref('base_revisionacteur') }}
    group by parent_id
)

select a.*,
    -- TODO : add lat and long, issue intrpreting double precision by dbt
    CAST(ST_X(a.location::geometry) AS DOUBLE PRECISION) AS latitude,
    CAST(ST_Y(a.location::geometry) AS DOUBLE PRECISION) AS longitude,
    e.enfants IS NOT NULL AS est_parent,
    e.enfants AS enfants_liste,
    jsonb_array_length(e.enfants) AS enfants_nombre,
    ca.identifiant_unique IS NOT NULL AS est_dans_carte,
    oa.identifiant_unique IS NOT NULL AS est_dans_opendata
from {{ ref('int_acteur') }} as a
LEFT JOIN enfants AS e
  ON a.identifiant_unique = e.parent_id
LEFT JOIN {{ ref('marts_carte_acteur') }} AS ca
  ON a.identifiant_unique = ca.identifiant_unique
LEFT JOIN {{ ref('marts_opendata_acteur') }} AS oa
  ON a.identifiant_unique = oa.identifiant_unique
