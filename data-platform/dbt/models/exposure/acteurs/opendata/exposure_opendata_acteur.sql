WITH deduplicated_opened_sources AS (
    SELECT
        da.uuid,
        string_agg(
            DISTINCT src.libelle, '|' ORDER BY src.libelle
        ) AS sources_list,
        -- from marts_opendata_acteur_sources, json source:identifiant_externe
        jsonb_agg(
            jsonb_build_object(src.libelle, das.identifiant_externe)
        ) AS identifiants_par_source
    FROM {{ ref('marts_opendata_acteur') }} AS da
    LEFT JOIN {{ ref('marts_opendata_acteur_sources') }} AS das
        ON da.identifiant_unique = das.acteur_id
    LEFT JOIN {{ ref('base_source') }} AS src
        ON das.source_id = src.id
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
                    FROM
                        {{ ref(
                            'marts_opendata_propositionservice_sous_categories'
                        ) }} AS pssc
                    INNER JOIN {{ ref('base_souscategorieobjet') }} AS sco
                        ON pssc.souscategorieobjet_id = sco.id
                    WHERE pssc.propositionservice_id = ps.id
                )
            )
        ) AS services
    FROM {{ ref('marts_opendata_acteur') }} AS da
    INNER JOIN {{ ref('marts_opendata_propositionservice') }} AS ps
        ON da.identifiant_unique = ps.acteur_id
    INNER JOIN {{ ref('base_action') }} AS a
        ON ps.action_id = a.id
    GROUP BY da.uuid
),

acteur_labels AS (
    SELECT
        da.uuid,
        string_agg(DISTINCT lq.code, '|' ORDER BY lq.code) AS labels
    FROM {{ ref('marts_opendata_acteur') }} AS da
    LEFT JOIN {{ ref('marts_opendata_acteur_labels') }} AS dal
        ON da.identifiant_unique = dal.acteur_id
    LEFT JOIN {{ ref('base_labelqualite') }} AS lq
        ON dal.labelqualite_id = lq.id
    GROUP BY da.uuid
),

acteur_services AS (
    SELECT
        da.uuid,
        string_agg(DISTINCT as2.code, '|' ORDER BY as2.code) AS services
    FROM {{ ref('marts_opendata_acteur') }} AS da
    LEFT JOIN {{ ref('marts_opendata_acteur_acteur_services') }} AS daas
        ON da.identifiant_unique = daas.acteur_id
    LEFT JOIN {{ ref('base_acteurservice') }} AS as2
        ON daas.acteurservice_id = as2.id
    GROUP BY da.uuid
),

perimetreadomicile AS (
    SELECT
        a.identifiant_unique
            AS acteur_id,
        -- get perimetreadomicile like a json list
        jsonb_agg(
            jsonb_build_object(
                'type', pad.type,
                'valeur', pad.valeur
            )
        )
            AS json_value
    FROM {{ ref('marts_opendata_acteur') }} AS a
    INNER JOIN {{ ref('marts_opendata_perimetreadomicile') }} AS pad
        ON a.identifiant_unique = pad.acteur_id
    GROUP BY a.identifiant_unique
)

SELECT
    da.uuid
        AS identifiant,
    CASE
        WHEN ds.sources_list IS NOT NULL
            THEN
                'Que faire de mes objets et déchets|ADEME|'
                || ds.sources_list
        ELSE 'Que faire de mes objets et déchets|ADEME'
    END
        AS paternite,
    ds.identifiants_par_source
        AS identifiants_des_contributeurs,
    da.nom,
    da.nom_commercial,
    da.siren,
    da.siret,
    da.description,
    acteur_type.code
        AS type_dacteur,
    da.url
        AS site_web,
    CASE
        WHEN da.telephone ~ '^0[67]' THEN NULL
        WHEN EXISTS (
            SELECT 1
            FROM {{ ref('marts_opendata_acteur_sources') }} AS das2
            INNER JOIN {{ ref('base_source') }} AS s
                ON das2.source_id = s.id
            WHERE
                das2.acteur_id = da.identifiant_unique
                AND s.code = 'carteco'
        ) THEN NULL
        ELSE da.telephone
    END
        AS telephone,
    -- Exclude addresses for actors 'A_DOMICILE'
    CASE
        WHEN da.lieu_prestation = 'A_DOMICILE' THEN NULL
        ELSE da.adresse
    END
        AS adresse,
    CASE
        WHEN da.lieu_prestation = 'A_DOMICILE' THEN NULL
        ELSE da.adresse_complement
    END
        AS complement_dadresse,
    da.code_postal,
    da.ville,
    da.code_commune_insee
        AS code_commune,
    aepci.code_epci,
    aepci.nom_epci,
    st_y(da.location::geometry)
        AS latitude,
    st_x(da.location::geometry)
        AS longitude,
    al.labels
        AS qualites_et_labels,
    da.public_accueilli,
    da.reprise,
    da.exclusivite_de_reprisereparation,
    da.uniquement_sur_rdv,
    acs.services
        AS type_de_services,
    da.consignes_dacces,
    da.horaires_description,
    da.horaires_osm,
    da.lieu_prestation,
    pad.json_value
        AS perimetreadomicile,
    ps.services::text
        AS propositions_de_services,
    {{ sscat_from_action('ps.services', 'emprunter') }}
        AS emprunter,
    {{ sscat_from_action('ps.services', 'preter') }}
        AS preter,
    {{ sscat_from_action('ps.services', 'louer') }}
        AS louer,
    {{ sscat_from_action('ps.services', 'mettreenlocation') }}
        AS mettreenlocation,
    {{ sscat_from_action('ps.services', 'reparer') }}
        AS reparer,
    {{ sscat_from_action('ps.services', 'donner') }}
        AS donner,
    {{ sscat_from_action('ps.services', 'trier') }}
        AS trier,
    {{ sscat_from_action('ps.services', 'echanger') }}
        AS echanger,
    {{ sscat_from_action('ps.services', 'revendre') }}
        AS revendre,
    {{ sscat_from_action('ps.services', 'acheter') }}
        AS acheter,
    {{ sscat_from_action('ps.services', 'rapporter') }}
        AS rapporter,
    to_char(da.modifie_le, 'YYYY-MM-DD')
        AS date_de_derniere_modification
FROM {{ ref('marts_opendata_acteur') }} AS da
LEFT JOIN {{ ref('base_acteur_type') }} AS acteur_type
    ON da.acteur_type_id = acteur_type.id
-- INNER JOIN : Only open lisense
INNER JOIN deduplicated_opened_sources AS ds
    ON da.uuid = ds.uuid
LEFT JOIN proposition_services AS ps
    ON da.uuid = ps.uuid
LEFT JOIN acteur_labels AS al
    ON da.uuid = al.uuid
LEFT JOIN acteur_services AS acs
    ON da.uuid = acs.uuid
LEFT JOIN perimetreadomicile AS pad
    ON da.identifiant_unique = pad.acteur_id
LEFT JOIN {{ ref('marts_opendata_acteur_epci') }} AS aepci
    ON da.identifiant_unique = aepci.identifiant_unique
ORDER BY da.uuid
