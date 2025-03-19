WITH deduplicated_opened_sources AS (
  SELECT
    da.uuid,
    string_agg(DISTINCT source.libelle, '|' ORDER BY source.libelle) as sources_list
  FROM {{ ref('marts_opendata_acteur') }}  AS da
  LEFT JOIN {{ ref('marts_opendata_acteur_sources') }} AS das
    ON da.id = das.acteur_id
  LEFT JOIN qfdmo_source AS source
    ON das.source_id = source.id
  GROUP BY da.uuid
),
proposition_services AS (
  SELECT
    da.uuid,
    jsonb_agg(
      jsonb_build_object(
        'action', a.code,
        'sous_categories', (
          SELECT jsonb_agg(sco.code)
          FROM {{ ref('marts_opendata_propositionservice_sous_categories') }}  AS pssc
          JOIN qfdmo_souscategorieobjet AS sco ON pssc.souscategorieobjet_id = sco.id
          WHERE pssc.propositionservice_id = ps.id
        )
      )
    ) as services
  FROM {{ ref('marts_opendata_acteur') }} AS da
  JOIN {{ ref('marts_opendata_propositionservice') }}  AS ps ON ps.acteur_id = da.id
  JOIN qfdmo_action AS a ON ps.action_id = a.id
  GROUP BY da.uuid
),
acteur_labels AS (
  SELECT
    da.uuid,
    string_agg(DISTINCT lq.code, '|' ORDER BY lq.code) as labels
  FROM {{ ref('marts_opendata_acteur') }}  AS da
  LEFT JOIN {{ ref('marts_opendata_acteur_labels') }} AS dal
    ON da.id = dal.acteur_id
  LEFT JOIN qfdmo_labelqualite AS lq ON dal.labelqualite_id = lq.id
  GROUP BY da.uuid
),
acteur_services AS (
  SELECT
    da.uuid,
    string_agg(DISTINCT as2.code, '|' ORDER BY as2.code) as services
  FROM {{ ref('marts_opendata_acteur') }}  AS da
  LEFT JOIN {{ ref('marts_opendata_acteur_acteur_services') }} AS daas
    ON da.id = daas.acteur_id
  LEFT JOIN qfdmo_acteurservice AS as2 ON daas.acteurservice_id = as2.id
  GROUP BY da.uuid
)
SELECT
  da.uuid as "identifiant",
  CASE
    WHEN ds.sources_list IS NOT NULL
    THEN 'Longue Vie Aux Objets|ADEME|' || ds.sources_list
    ELSE 'Longue Vie Aux Objets|ADEME'
  END as "paternite",
  da.nom as "nom",
  da.nom_commercial as "nom_commercial",
  da.siren as "siren",
  da.siret as "siret",
  da.description as "description",
  at.code as "type_acteur",
  da.url as "site_web",
  CASE
    WHEN da.telephone ~ '^0[67]' THEN NULL
    WHEN EXISTS (
      SELECT 1
      FROM {{ ref('marts_opendata_acteur_sources') }} das2
      JOIN qfdmo_source s ON das2.source_id = s.id
      WHERE das2.acteur_id = da.id
      AND s.code = 'carteco'
    ) THEN NULL
    ELSE da.telephone
  END as "telephone",
  da.adresse as "adresse",
  da.adresse_complement as "complement_adresse",
  da.code_postal as "code_postal",
  da.ville as "ville",
  ST_Y(da.location::geometry) as "latitude",
  ST_X(da.location::geometry) as "longitude",
  al.labels as "qualites_labels",
  da.public_accueilli as "public_accueilli",
  da.reprise as "reprise",
  da.exclusivite_de_reprisereparation as "exclusivite_reprise",
  da.uniquement_sur_rdv as "uniquement_sur_rdv",
  acs.services as "type_services",
  ps.services::text as "propositions_services",
  to_char(da.modifie_le, 'YYYY-MM-DD') as "date_modification"
FROM {{ ref('marts_opendata_acteur') }}  AS da
LEFT JOIN qfdmo_acteurtype AS at ON da.acteur_type_id = at.id
-- INNER JOIN : Only open lisense
INNER JOIN deduplicated_opened_sources AS ds ON da.uuid = ds.uuid
LEFT JOIN proposition_services AS ps ON da.uuid = ps.uuid
LEFT JOIN acteur_labels AS al ON da.uuid = al.uuid
LEFT JOIN acteur_services AS acs ON da.uuid = acs.uuid
WHERE da.statut = 'ACTIF'
AND da.public_accueilli NOT IN ('AUCUN', 'PROFESSIONNELS')
AND da.id NOT LIKE '%_reparation_%'
ORDER BY da.uuid