# Generated by Django 5.1.4 ON 2025-02-03 13:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0125_extension_uuid_ossp"),
    ]

    operations = [
        migrations.RunSQL(
            """
DROP VIEW IF EXISTS qfdmo_vueacteur;

CREATE VIEW qfdmo_vueacteur AS (
    SELECT
        da.uuid AS uuid,
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
    LEFT JOIN qfdmo_displayedacteur AS da
      ON a.identifiant_unique = da.identifiant_unique
);
""",
            reverse_sql="""
DROP VIEW IF EXISTS qfdmo_vueacteur;
""",
        ),
    ]
