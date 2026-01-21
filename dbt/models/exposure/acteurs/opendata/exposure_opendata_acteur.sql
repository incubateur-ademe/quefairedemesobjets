WITH deduplicated_opened_sources AS (
  SELECT
    da.uuid,
    string_agg(DISTINCT source.libelle, '|' ORDER BY source.libelle) as sources_list,
    -- from marts_opendata_acteur_sources, get json with source_code:identifiant_externe
    jsonb_agg(jsonb_build_object(source.libelle, das.identifiant_externe)) as identifiants_par_source
  FROM {{ ref('marts_opendata_acteur') }}  AS da
  LEFT JOIN {{ ref('marts_opendata_acteur_sources') }} AS das
    ON da.identifiant_unique = das.acteur_id
  LEFT JOIN {{ source('qfdmo', 'qfdmo_source') }} AS source
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
          JOIN {{ source('qfdmo', 'qfdmo_souscategorieobjet') }} AS sco ON pssc.souscategorieobjet_id = sco.id
          WHERE pssc.propositionservice_id = ps.id
        )
      )
    ) as services
  FROM {{ ref('marts_opendata_acteur') }} AS da
  JOIN {{ ref('marts_opendata_propositionservice') }}  AS ps ON ps.acteur_id = da.identifiant_unique
  JOIN {{ source('qfdmo', 'qfdmo_action') }} AS a ON ps.action_id = a.id
  GROUP BY da.uuid
),
acteur_labels AS (
  SELECT
    da.uuid,
    string_agg(DISTINCT lq.code, '|' ORDER BY lq.code) as labels
  FROM {{ ref('marts_opendata_acteur') }}  AS da
  LEFT JOIN {{ ref('marts_opendata_acteur_labels') }} AS dal
    ON da.identifiant_unique = dal.acteur_id
  LEFT JOIN {{ source('qfdmo', 'qfdmo_labelqualite') }} AS lq ON dal.labelqualite_id = lq.id
  GROUP BY da.uuid
),
acteur_services AS (
  SELECT
    da.uuid,
    string_agg(DISTINCT as2.code, '|' ORDER BY as2.code) as services
  FROM {{ ref('marts_opendata_acteur') }}  AS da
  LEFT JOIN {{ ref('marts_opendata_acteur_acteur_services') }} AS daas
    ON da.identifiant_unique = daas.acteur_id
  LEFT JOIN {{ source('qfdmo', 'qfdmo_acteurservice') }} AS as2 ON daas.acteurservice_id = as2.id
  GROUP BY da.uuid
),
perimetreadomicile AS (
  SELECT
    a.identifiant_unique AS acteur_id,
    -- get perimetreadomicile like a json list
    jsonb_agg(
      jsonb_build_object(
        'type', pad.type,
        'valeur', pad.valeur
      )
    ) as json_value
  FROM {{ ref('marts_opendata_acteur') }} AS a
  INNER JOIN {{ ref('marts_opendata_perimetreadomicile') }} AS pad ON pad.acteur_id = a.identifiant_unique
  GROUP BY a.identifiant_unique
)
SELECT
  da.uuid as "identifiant",
  CASE
    WHEN ds.sources_list IS NOT NULL
    THEN 'Longue Vie Aux Objets|ADEME|' || ds.sources_list
    ELSE 'Longue Vie Aux Objets|ADEME'
  END as "paternite",
  ds.identifiants_par_source as "identifiants_des_contributeurs",
  da.nom as "nom",
  da.nom_commercial as "nom_commercial",
  da.siren as "siren",
  da.siret as "siret",
  da.description as "description",
  at.code as "type_dacteur",
  da.url as "site_web",
  CASE
    WHEN da.telephone ~ '^0[67]' THEN NULL
    WHEN EXISTS (
      SELECT 1
      FROM {{ ref('marts_opendata_acteur_sources') }} das2
      JOIN {{ source('qfdmo', 'qfdmo_source') }} s ON das2.source_id = s.id
      WHERE das2.acteur_id = da.identifiant_unique
      AND s.code = 'carteco'
    ) THEN NULL
    ELSE da.telephone
  END as "telephone",
  da.adresse as "adresse",
  da.adresse_complement as "complement_dadresse",
  da.code_postal as "code_postal",
  da.ville as "ville",
  da.code_commune_insee as "code_commune",
  aepci.code_epci as "code_epci",
  aepci.nom_epci as "nom_epci",
  ST_Y(da.location::geometry) as "latitude",
  ST_X(da.location::geometry) as "longitude",
  al.labels as "qualites_et_labels",
  da.public_accueilli as "public_accueilli",
  da.reprise as "reprise",
  da.exclusivite_de_reprisereparation as "exclusivite_de_reprisereparation",
  da.uniquement_sur_rdv as "uniquement_sur_rdv",
  acs.services as "type_de_services",
  da.consignes_dacces as "consignes_dacces",
  da.horaires_description as "horaires_description",
  da.horaires_osm as "horaires_osm",
  da.lieu_prestation as "lieu_prestation",
  pad.json_value as "perimetreadomicile",
  ps.services::text as "propositions_de_services",
  {{ sscat_from_action('ps.services', 'emprunter') }} as "emprunter",
  {{ sscat_from_action('ps.services', 'preter') }} as "preter",
  {{ sscat_from_action('ps.services', 'louer') }} as "louer",
  {{ sscat_from_action('ps.services', 'mettreenlocation') }} as "mettreenlocation",
  {{ sscat_from_action('ps.services', 'reparer') }} as "reparer",
  {{ sscat_from_action('ps.services', 'donner') }} as "donner",
  {{ sscat_from_action('ps.services', 'trier') }} as "trier",
  {{ sscat_from_action('ps.services', 'echanger') }} as "echanger",
  {{ sscat_from_action('ps.services', 'revendre') }} as "revendre",
  {{ sscat_from_action('ps.services', 'acheter') }} as "acheter",
  {{ sscat_from_action('ps.services', 'rapporter') }} as "rapporter",
  to_char(da.modifie_le, 'YYYY-MM-DD') as "date_de_derniere_modification"
FROM {{ ref('marts_opendata_acteur') }}  AS da
LEFT JOIN {{ source('qfdmo', 'qfdmo_acteurtype') }} AS at ON da.acteur_type_id = at.id
-- INNER JOIN : Only open lisense
INNER JOIN deduplicated_opened_sources AS ds ON da.uuid = ds.uuid
LEFT JOIN proposition_services AS ps ON da.uuid = ps.uuid
LEFT JOIN acteur_labels AS al ON da.uuid = al.uuid
LEFT JOIN acteur_services AS acs ON da.uuid = acs.uuid
LEFT JOIN perimetreadomicile AS pad ON da.identifiant_unique = pad.acteur_id
LEFT JOIN {{ ref('marts_opendata_acteur_epci') }} AS aepci ON da.identifiant_unique = aepci.identifiant_unique
ORDER BY da.uuid
