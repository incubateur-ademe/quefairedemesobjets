from dags.views.view_acteur_tous import VIEW_NAME


def view_acteur_tous_sql_generate() -> str:
    """Génère le code SQL de la vue matérialisé
    en faisant python dags/views/view_acteur_tous.py

    Pour tester et finaliser la vue:
    - placer le code dans le fichier dédié ./sql/view_acteur_tous.sql
    - la formatter et pouvoir la relire plus facilement
    - tester avec un client SQL

    Au final on à le code SQL définitif dans notre repo pour le versionning
    """
    # Champs communs à toutes les tables, on prend au mieux avec COALESCE
    fields_on_all = [
        # IDs
        "identifiant_unique",
        "identifiant_externe",
        "acteur_type_id",
        "source_id",
        "action_principale_id",
        # Noms
        "nom",
        "nom_commercial",
        "nom_officiel",
        # GEO
        "adresse",
        "adresse_complement",
        "code_postal",
        "location",
        "ville",
        # Contact
        "telephone",
        "email",
        "url",
        "horaires_description",
        "horaires_osm",
        "uniquement_sur_rdv",
        # MISC
        "statut",
        "naf_principal",
        "siret",
        "public_accueilli",
        "exclusivite_de_reprisereparation",
    ]
    selected = ",\n".join(
        [f"COALESCE(da.{x}, ra.{x}, a.{x}) AS {x}" for x in fields_on_all]
    )
    # dernier champ sélectionné: parent_id qui n'existe que dans revisionacteur
    selected += ",\nra.parent_id AS parent_id,\n"
    selected += """-- Si l'identifiant est dans parent_ids, alors c'est un parent
            CASE
                WHEN COALESCE(
                    da.identifiant_unique,
                    ra.identifiant_unique,
                    a.identifiant_unique)
                    IN (SELECT id FROM parent_ids) THEN TRUE
                ELSE FALSE
            END AS est_parent,\n"""
    selected += """da.identifiant_unique IS NOT NULL AS est_dans_displayedacteur,
                    ra.identifiant_unique IS NOT NULL AS est_dans_revisionacteur,
                    a.identifiant_unique IS NOT NULL AS est_dans_acteur"""

    query = f"""
    -- Il n'existe pas aujourdhui de CREATE OR REPLACE MATERIALIZED VIEW
    -- d'où l'autre requête DROP IF EXISTS avant de créer
    CREATE MATERIALIZED VIEW {VIEW_NAME} AS (
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
                {selected}
                    FROM qfdmo_displayedacteur AS da
                    FULL OUTER JOIN qfdmo_revisionacteur AS ra
                        ON da.identifiant_unique = ra.identifiant_unique
                    FULL OUTER JOIN qfdmo_acteur AS a
                        ON da.identifiant_unique = a.identifiant_unique
        )
        SELECT
            -- ne pas faire un lazy * car ceci sélectionne des champs génériques
            -- présents sur plusieurs tables (ex: url) ce qui cause des erreurs
            acteur_all.*,
            ST_Y(acteur_all.location) AS location_lat,
            ST_X(acteur_all.location) AS location_long,
            -- Infos enfants pour les parents
            CASE
                WHEN est_parent THEN (SELECT
                    enfants_nombre
                    FROM parent_ids_to_enfants
                    WHERE parent_id = acteur_all.identifiant_unique)
                ELSE NULL
            END AS enfants_nombre,
            CASE
                WHEN est_parent THEN (SELECT
                    enfants_liste
                    FROM parent_ids_to_enfants
                    WHERE parent_id = acteur_all.identifiant_unique)
                ELSE NULL
            END AS enfants_liste,
            -- Les codes pour être plus pratique ques les ids
            s.code AS source_code,
            atype.code AS acteur_type_code
        FROM acteur_all
        LEFT JOIN qfdmo_source AS s ON s.id = acteur_all.source_id
        LEFT JOIN qfdmo_acteurtype AS atype ON atype.id = acteur_all.acteur_type_id
    )"""
    return query


# Pour générer le code SQL de la vue
# python dags/views/generators/view_acteur_tous.py
# voir commentaire de la fonction sql_view_generate_code
# pour les étapes suivantes
if __name__ == "__main__":
    print("Requête SQL générée:")
    print(view_acteur_tous_sql_generate())
