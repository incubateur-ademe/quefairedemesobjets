# Generated by Django 4.2.6 on 2023-10-23 04:50

import django.contrib.gis.db.models.fields
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("qfdmo", "0021_remove_acteur_source_donnee_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="acteur",
            name="cree_le",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="acteur",
            name="modifie_le",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="acteur",
            name="naf_principal",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="revisionacteur",
            name="cree_le",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="revisionacteur",
            name="modifie_le",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="revisionacteur",
            name="naf_principal",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.CreateModel(
            name="CorrectionActeur",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("nom", models.CharField(max_length=255)),
                ("adresse", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "adresse_complement",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("code_postal", models.CharField(blank=True, max_length=10, null=True)),
                ("ville", models.CharField(blank=True, max_length=255, null=True)),
                ("url", models.CharField(blank=True, max_length=2048, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, null=True, srid=4326
                    ),
                ),
                ("telephone", models.CharField(blank=True, max_length=255, null=True)),
                ("multi_base", models.BooleanField(default=False)),
                (
                    "nom_commercial",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "nom_officiel",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("manuel", models.BooleanField(default=False)),
                ("label_reparacteur", models.BooleanField(default=False)),
                ("siret", models.CharField(blank=True, max_length=14, null=True)),
                (
                    "identifiant_externe",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("ACTIF", "actif"),
                            ("INACTIF", "inactif"),
                            ("SUPPRIME", "supprimé"),
                        ],
                        default="ACTIF",
                        max_length=255,
                    ),
                ),
                (
                    "naf_principal",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
                ("identifiant_unique", models.CharField(max_length=255)),
                ("source", models.CharField(max_length=255)),
                ("resultat_brute_source", models.JSONField()),
                (
                    "correction_statut",
                    models.CharField(
                        choices=[
                            ("ACTIF", "actif"),
                            ("IGNORE", "ignoré"),
                            ("ACCEPTE", "accepté"),
                            ("REJETE", "rejeté"),
                        ],
                        default="ACTIF",
                        max_length=255,
                    ),
                ),
                (
                    "acteur_type",
                    models.ForeignKey(
                        blank=True,
                        default=None,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.acteurtype",
                    ),
                ),
                (
                    "final_acteur",
                    models.ForeignKey(
                        db_constraint=False,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        related_name="corrections",
                        to="qfdmo.finalacteur",
                        to_field="identifiant_unique",
                    ),
                ),
            ],
            options={
                "verbose_name": "Proposition de correction d'un acteur",
                "verbose_name_plural": "Propositions de correction des acteurs",
            },
        ),
        migrations.RunSQL(
            """
            DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalacteur;
            CREATE MATERIALIZED VIEW qfdmo_finalacteur AS
                SELECT
                      COALESCE(ra.id, a.id) as id
                    , COALESCE(ra.nom, a.nom) as nom
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
                FROM qfdmo_acteur a
                LEFT OUTER JOIN qfdmo_revisionacteur AS ra ON ra.id = a.id;
                CREATE UNIQUE INDEX ON qfdmo_finalacteur(id);
            """,
            """
            DROP MATERIALIZED VIEW IF EXISTS qfdmo_finalacteur;
            CREATE MATERIALIZED VIEW qfdmo_finalacteur AS
                SELECT
                      COALESCE(ra.id, a.id) as id
                    , COALESCE(ra.nom, a.nom) as nom
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
                FROM qfdmo_acteur a
                LEFT OUTER JOIN qfdmo_revisionacteur AS ra ON ra.id = a.id;
                CREATE UNIQUE INDEX ON qfdmo_finalacteur(id);
            """,
        ),
    ]
