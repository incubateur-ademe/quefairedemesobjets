CREATE MATERIALIZED VIEW IF NOT EXISTS qfdmo_vue_acteur_tous AS (
    WITH
        parent_ids AS (
            SELECT DISTINCT
                parent_id AS id
            FROM
                qfdmo_revisionacteur
        ),
        parent_ids_to_enfants AS (
            SELECT
                parent_id,
                ARRAY_AGG (identifiant_unique) AS enfants_liste,
                CARDINALITY(ARRAY_AGG (identifiant_unique)) AS enfants_nombre
            FROM
                qfdmo_revisionacteur AS ra
            WHERE
                parent_id IS NOT NULL
            GROUP BY
                1
            ORDER BY
                3 DESC
        ),
        acteur_all AS (
            SELECT
                COALESCE(
                    da.identifiant_unique,
                    ra.identifiant_unique,
                    a.identifiant_unique
                ) AS identifiant_unique,
                COALESCE(
                    da.identifiant_externe,
                    ra.identifiant_externe,
                    a.identifiant_externe
                ) AS identifiant_externe,
                COALESCE(
                    da.acteur_type_id,
                    ra.acteur_type_id,
                    a.acteur_type_id
                ) AS acteur_type_id,
                COALESCE(da.source_id, ra.source_id, a.source_id) AS source_id,
                COALESCE(
                    da.action_principale_id,
                    ra.action_principale_id,
                    a.action_principale_id
                ) AS action_principale_id,
                COALESCE(da.nom, ra.nom, a.nom) AS nom,
                COALESCE(
                    da.nom_commercial,
                    ra.nom_commercial,
                    a.nom_commercial
                ) AS nom_commercial,
                COALESCE(da.nom_officiel, ra.nom_officiel, a.nom_officiel) AS nom_officiel,
                COALESCE(da.adresse, ra.adresse, a.adresse) AS adresse,
                COALESCE(
                    da.adresse_complement,
                    ra.adresse_complement,
                    a.adresse_complement
                ) AS adresse_complement,
                COALESCE(da.code_postal, ra.code_postal, a.code_postal) AS code_postal,
                COALESCE(da.location, ra.location, a.location) AS location,
                COALESCE(da.ville, ra.ville, a.ville) AS ville,
                COALESCE(da.telephone, ra.telephone, a.telephone) AS telephone,
                COALESCE(da.email, ra.email, a.email) AS email,
                COALESCE(da.url, ra.url, a.url) AS url,
                COALESCE(
                    da.horaires_description,
                    ra.horaires_description,
                    a.horaires_description
                ) AS horaires_description,
                COALESCE(da.horaires_osm, ra.horaires_osm, a.horaires_osm) AS horaires_osm,
                COALESCE(
                    da.uniquement_sur_rdv,
                    ra.uniquement_sur_rdv,
                    a.uniquement_sur_rdv
                ) AS uniquement_sur_rdv,
                COALESCE(da.statut, ra.statut, a.statut) AS statut,
                COALESCE(
                    da.naf_principal,
                    ra.naf_principal,
                    a.naf_principal
                ) AS naf_principal,
                COALESCE(da.siret, ra.siret, a.siret) AS siret,
                COALESCE(
                    da.public_accueilli,
                    ra.public_accueilli,
                    a.public_accueilli
                ) AS public_accueilli,
                COALESCE(
                    da.exclusivite_de_reprisereparation,
                    ra.exclusivite_de_reprisereparation,
                    a.exclusivite_de_reprisereparation
                ) AS exclusivite_de_reprisereparation,
                ra.parent_id AS parent_id,
                -- Si l'identifiant est dans la liste des parent_ids, alors c'est un parent
                CASE
                    WHEN COALESCE(
                        da.identifiant_unique,
                        ra.identifiant_unique,
                        a.identifiant_unique
                    ) IN (
                        SELECT
                            id
                        FROM
                            parent_ids
                    ) THEN TRUE
                    ELSE FALSE
                END AS est_parent,
                da.identifiant_unique IS NOT NULL AS est_dans_displayedacteur,
                ra.identifiant_unique IS NOT NULL AS est_dans_revisionacteur,
                a.identifiant_unique IS NOT NULL AS est_dans_acteur
            FROM
                qfdmo_displayedacteur AS da
                FULL OUTER JOIN qfdmo_revisionacteur AS ra ON da.identifiant_unique = ra.identifiant_unique
                FULL OUTER JOIN qfdmo_acteur AS a ON da.identifiant_unique = a.identifiant_unique
        )
    SELECT
        -- ne pas faire un lazy * car ceci sélectionne des champs génériques
        -- présents sur plusieurs tables (ex: url) ce qui cause des erreurs
        acteur_all.*,
        ST_Y (acteur_all.location) AS location_lat,
        ST_X (acteur_all.location) AS location_long,
        -- Info enfants pour les parents
        CASE
            WHEN est_parent THEN (
                SELECT
                    enfants_nombre
                FROM
                    parent_ids_to_enfants
                WHERE
                    parent_id = acteur_all.identifiant_unique
            )
            ELSE NULL
        END AS enfants_nombre,
        CASE
            WHEN est_parent THEN (
                SELECT
                    enfants_liste
                FROM
                    parent_ids_to_enfants
                WHERE
                    parent_id = acteur_all.identifiant_unique
            )
            ELSE NULL
        END AS enfants_liste,
        -- Les codes pour être plus pratique ques les ids
        s.code AS source_code,
        atype.code AS acteur_type_code
    FROM
        acteur_all
        LEFT JOIN qfdmo_source AS s ON s.id = acteur_all.source_id
        LEFT JOIN qfdmo_acteurtype AS atype ON atype.id = acteur_all.acteur_type_id
);