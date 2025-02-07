# Generated by Django 5.1.4 ON 2025-02-03 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0118_toutacteur"),
    ]

    operations = [
        migrations.RunSQL(
            """
DROP VIEW IF EXISTS qfdmo_toutacteur;

CREATE VIEW qfdmo_toutacteur AS (
    SELECT
        COALESCE(ra.identifiant_unique, a.identifiant_unique) AS identifiant_unique,
        COALESCE(ra.nom, a.nom) AS nom,
        COALESCE(ra.description, a.description) AS description,
        COALESCE(ra.acteur_type_id, a.acteur_type_id) AS acteur_type_id,
        COALESCE(ra.adresse, a.adresse) AS adresse,
        COALESCE(ra.adresse_complement, a.adresse_complement) AS adresse_complement,
        COALESCE(ra.code_postal, a.code_postal) AS code_postal,
        COALESCE(ra.ville, a.ville) AS ville,
        COALESCE(ra.url, a.url) AS url,
        COALESCE(ra.email, a.email) AS email,
        COALESCE(ra.location, a.location) AS location,
        COALESCE(ra.telephone, a.telephone) AS telephone,
        COALESCE(ra.nom_commercial, a.nom_commercial) AS nom_commercial,
        COALESCE(ra.nom_officiel, a.nom_officiel) AS nom_officiel,
        COALESCE(ra.siren, a.siren) AS siren,
        COALESCE(ra.siret, a.siret) AS siret,
        COALESCE(ra.source_id, a.source_id) AS source_id,
        COALESCE(ra.identifiant_externe, a.identifiant_externe) AS identifiant_externe,
        COALESCE(ra.statut, a.statut) AS statut,
        COALESCE(ra.naf_principal, a.naf_principal) AS naf_principal,
        COALESCE(ra.commentaires, a.commentaires) AS commentaires,
        COALESCE(ra.horaires_osm, a.horaires_osm) AS horaires_osm,
        COALESCE(ra.horaires_description, a.horaires_description) AS horaires_description,
        COALESCE(ra.public_accueilli, a.public_accueilli) AS public_accueilli,
        COALESCE(ra.reprise, a.reprise) AS reprise,
        COALESCE(ra.exclusivite_de_reprisereparation, a.exclusivite_de_reprisereparation) AS exclusivite_de_reprisereparation,
        COALESCE(ra.uniquement_sur_rdv, a.uniquement_sur_rdv) AS uniquement_sur_rdv,
        COALESCE(ra.action_principale_id, a.action_principale_id) AS action_principale_id,
        COALESCE(ra.modifie_le, a.modifie_le) AS modifie_le,
        ra.parent_id AS parent_id,
        COALESCE(a.cree_le, ra.cree_le) AS cree_le
    FROM qfdmo_acteur AS a
    FULL JOIN qfdmo_revisionacteur AS ra
    ON a.identifiant_unique = ra.identifiant_unique
);
""",
            reverse_sql="""
DROP VIEW IF EXISTS qfdmo_toutacteur;
""",
        ),
        migrations.RunSQL(
            """
DROP VIEW IF EXISTS qfdmo_toutacteur_labels;

-- Créer la vue
CREATE VIEW qfdmo_toutacteur_labels AS (
    SELECT
        CASE
            WHEN ra.identifiant_unique IS NULL THEN al.id
            ELSE ral.id
        END AS id,
        CASE
            WHEN ra.identifiant_unique IS NOT NULL THEN ral.revisionacteur_id
            ELSE al.acteur_id
        END AS toutacteur_id,
        CASE
            WHEN ra.identifiant_unique IS NOT NULL THEN ral.labelqualite_id
            ELSE al.labelqualite_id
        END AS labelqualite_id
    FROM qfdmo_acteur_labels AS al
    LEFT JOIN qfdmo_revisionacteur_labels AS ral
        ON al.acteur_id = ral.revisionacteur_id --was FULL JOIN
    LEFT JOIN qfdmo_revisionacteur AS ra ON al.acteur_id = ra.identifiant_unique
    WHERE CASE
            WHEN ra.identifiant_unique IS NULL THEN al.id
            ELSE ral.id
        END  is not null
);
""",
            reverse_sql="""
DROP VIEW IF EXISTS qfdmo_toutacteur_labels;
""",
        ),
        migrations.RunSQL(
            """
DROP VIEW IF EXISTS qfdmo_toutacteur_acteur_services;

CREATE VIEW qfdmo_toutacteur_acteur_services AS (
    SELECT
        CASE
            WHEN ra.identifiant_unique IS NULL THEN aas.id
            ELSE raas.id
        END AS id,
        CASE
            WHEN ra.identifiant_unique IS NOT NULL THEN raas.revisionacteur_id
            ELSE aas.acteur_id
        END AS toutacteur_id,
        CASE
            WHEN ra.identifiant_unique IS NOT NULL THEN raas.acteurservice_id
            ELSE aas.acteurservice_id
        END AS acteurservice_id
    FROM qfdmo_acteur_acteur_services AS aas
    LEFT JOIN qfdmo_revisionacteur_acteur_services AS raas
        ON aas.acteur_id = raas.revisionacteur_id --was FULL JOIN
    LEFT JOIN qfdmo_revisionacteur AS ra ON aas.acteur_id = ra.identifiant_unique
    WHERE CASE
            WHEN ra.identifiant_unique IS NULL THEN aas.id
            ELSE raas.id
        END  is not null
);
""",
            reverse_sql="""
DROP VIEW IF EXISTS qfdmo_toutacteur_acteur_services;
""",
        ),
        migrations.RunSQL(
            """
DROP VIEW IF EXISTS qfdmo_toutpropositionservice;

-- Créer la vue
CREATE VIEW qfdmo_toutpropositionservice AS (
    SELECT
        CASE
            WHEN ra.identifiant_unique IS NULL THEN CONCAT('PS_', ps.id::text)
            ELSE CONCAT('RPS_', rps.id::text)
        END AS id,
        CASE
            WHEN ra.identifiant_unique IS NOT NULL THEN rps.acteur_id
            ELSE ps.acteur_id
        END AS acteur_id,
        CASE
            WHEN ra.identifiant_unique IS NOT NULL THEN rps.action_id
            ELSE ps.action_id
        END AS action_id,
        CASE
            WHEN ra.identifiant_unique IS NULL THEN ps.id
            ELSE rps.id
        END AS ext_id,
        CASE
            WHEN ra.identifiant_unique IS NULL THEN false
            ELSE true
        END AS est_revision
    FROM qfdmo_propositionservice AS ps
    LEFT JOIN qfdmo_revisionpropositionservice AS rps
        ON ps.acteur_id = rps.acteur_id --was FULL JOIN
    LEFT JOIN qfdmo_revisionacteur AS ra ON ps.acteur_id = ra.identifiant_unique
    WHERE CASE
            WHEN ra.identifiant_unique IS NULL THEN ps.id
            ELSE rps.id
        END is not null
);
""",
            reverse_sql="""
DROP VIEW IF EXISTS qfdmo_toutpropositionservice;
""",
        ),
        migrations.RunSQL(
            """
DROP VIEW IF EXISTS qfdmo_toutpropositionservice_sous_categories;

-- Créer la vue
CREATE VIEW qfdmo_toutpropositionservice_sous_categories AS (
    SELECT
        CONCAT(tps.id, '_', pssscat.id::text, '_', pssscat.id::text) AS id,
        CASE
            WHEN tps.est_revision IS TRUE
            THEN CONCAT('RPS_', rpssscat.revisionpropositionservice_id::text)
            ELSE CONCAT('PS_', pssscat.propositionservice_id::text)
        END AS toutpropositionservice_id,
        CASE
            WHEN tps.est_revision IS TRUE
            THEN rpssscat.souscategorieobjet_id
            ELSE pssscat.souscategorieobjet_id
        END AS souscategorieobjet_id
    FROM qfdmo_toutpropositionservice AS tps
    LEFT JOIN qfdmo_propositionservice_sous_categories AS pssscat
        ON tps.ext_id = pssscat.propositionservice_id AND tps.est_revision = false
    LEFT JOIN qfdmo_revisionpropositionservice_sous_categories AS rpssscat
        ON tps.ext_id = rpssscat.revisionpropositionservice_id
            AND tps.est_revision = true
);
""",
            reverse_sql="""
DROP VIEW IF EXISTS qfdmo_toutpropositionservice_sous_categories;
""",
        ),
    ]
