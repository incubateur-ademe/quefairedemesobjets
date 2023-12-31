# Generated by Django 4.2.6 on 2023-10-27 08:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("qfdmo", "0025_alter_propositionservice_acteur_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="acteur",
            name="id",
        ),
        migrations.RemoveField(
            model_name="revisionacteur",
            name="id",
        ),
        migrations.AlterField(
            model_name="acteur",
            name="identifiant_unique",
            field=models.CharField(
                blank=True,
                max_length=255,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="correctionacteur",
            name="id",
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="propositionservice",
            name="acteur",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="proposition_services",
                to="qfdmo.acteur",
            ),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="identifiant_unique",
            field=models.CharField(
                blank=True,
                max_length=255,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
        migrations.AlterField(
            model_name="revisionpropositionservice",
            name="revision_acteur",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="proposition_services",
                to="qfdmo.revisionacteur",
            ),
        ),
        migrations.RunSQL(
            """
                    DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalacteur;
                    CREATE MATERIALIZED VIEW qfdmo_finalacteur AS
                        SELECT
                            COALESCE(ra.nom, a.nom) as nom
                            , COALESCE(ra.identifiant_unique, a.identifiant_unique) as identifiant_unique
                            , COALESCE(ra.acteur_type_id, a.acteur_type_id) as acteur_type_id
                            , COALESCE(ra.adresse, a.adresse) as adresse
                            , COALESCE(ra.adresse_complement, a.adresse_complement) as adresse_complement
                            , COALESCE(ra.code_postal, a.code_postal) as code_postal
                            , COALESCE(ra.ville, a.ville) as ville
                            , COALESCE(ra.url, a.url) as url
                            , COALESCE(ra.email, a.email) as email
                            , COALESCE(ra.location, a.location) as location
                            , COALESCE(ra.telephone, a.telephone) as telephone
                            , COALESCE(ra.multi_base, a.multi_base) as multi_base
                            , COALESCE(ra.nom_commercial, a.nom_commercial) as nom_commercial
                            , COALESCE(ra.nom_officiel, a.nom_officiel) as nom_officiel
                            , COALESCE(ra.manuel, a.manuel) as manuel
                            , COALESCE(ra.label_reparacteur, a.label_reparacteur) as label_reparacteur
                            , COALESCE(ra.siret, a.siret) as siret
                            , COALESCE(ra.source_id, a.source_id) as source_id
                            , COALESCE(ra.identifiant_externe, a.identifiant_externe) as identifiant_externe
                            , COALESCE(ra.statut, a.statut) as statut
                            , COALESCE(ra.cree_le, a.cree_le) as cree_le
                            , COALESCE(ra.modifie_le, a.modifie_le) as modifie_le
                            , COALESCE(ra.naf_principal, a.naf_principal) as naf_principal
                            , COALESCE(ra.commentaires, a.commentaires) as commentaires
                        FROM qfdmo_acteur a
                        LEFT OUTER JOIN qfdmo_revisionacteur AS ra ON ra.identifiant_unique = a.identifiant_unique;
                    CREATE UNIQUE INDEX ON qfdmo_finalacteur(identifiant_unique);

                    DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalpropositionservice;
                    CREATE MATERIALIZED VIEW qfdmo_finalpropositionservice AS
                        SELECT row_number() OVER (ORDER BY a.identifiant_unique) as id,
                            a.identifiant_unique AS acteur_id,
                            COALESCE(rps.action_id, ps.action_id) AS action_id,
                            COALESCE(rps.acteur_service_id, ps.acteur_service_id) AS acteur_service_id
                        FROM qfdmo_acteur AS a
                        LEFT OUTER JOIN qfdmo_revisionacteur AS ra ON a.identifiant_unique = ra.identifiant_unique
                        LEFT OUTER JOIN qfdmo_propositionservice AS ps ON ps.acteur_id = a.identifiant_unique AND ra.identifiant_unique IS NULL
                        LEFT OUTER JOIN qfdmo_revisionpropositionservice AS rps ON rps.revision_acteur_id = a.identifiant_unique;
                    CREATE UNIQUE INDEX ON qfdmo_finalpropositionservice(id);

                    DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalpropositionservice_sous_categories;
                    CREATE MATERIALIZED VIEW qfdmo_finalpropositionservice_sous_categories AS
                        SELECT row_number() OVER (ORDER BY a.identifiant_unique) as id,
                        	fps.id AS finalpropositionservice_id,
                            COALESCE(rps_sc.souscategorieobjet_id, ps_sc.souscategorieobjet_id) AS souscategorieobjet_id
                        FROM qfdmo_acteur AS a
                        LEFT OUTER JOIN qfdmo_revisionacteur AS ra ON a.identifiant_unique = ra.identifiant_unique
                        LEFT OUTER JOIN qfdmo_propositionservice AS ps ON ps.acteur_id = a.identifiant_unique AND ra.identifiant_unique IS NULL
                        LEFT OUTER JOIN qfdmo_revisionpropositionservice AS rps ON rps.revision_acteur_id = a.identifiant_unique
                        LEFT OUTER JOIN qfdmo_finalpropositionservice AS fps ON fps.acteur_id = a.identifiant_unique AND fps.action_id = COALESCE(rps.action_id, ps.action_id) and COALESCE(rps.acteur_service_id, ps.acteur_service_id) = fps.acteur_service_id
                        LEFT OUTER JOIN qfdmo_propositionservice_sous_categories AS ps_sc ON ps_sc.propositionservice_id = ps.id AND ps.id IS NOT NULL
                        LEFT OUTER JOIN qfdmo_revisionpropositionservice_sous_categories AS rps_sc ON rps_sc.revisionpropositionservice_id = rps.id AND rps.id IS NOT NULL
                        WHERE (rps_sc.revisionpropositionservice_id IS NOT NULL OR ps_sc.propositionservice_id IS NOT NULL);
                    CREATE UNIQUE INDEX ON qfdmo_finalpropositionservice_sous_categories(id);
            """,
            """
            DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalpropositionservice_sous_categories;
            DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalpropositionservice;
            DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalacteur;
            """,
        ),
    ]
