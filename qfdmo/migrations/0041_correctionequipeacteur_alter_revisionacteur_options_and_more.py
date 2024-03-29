# Generated by Django 4.2.9 on 2024-02-26 15:55

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models

import qfdmo.models.acteur


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0040_displayedacteur_alter_finalacteur_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CorrectionEquipeActeur",
            fields=[
                ("description", models.TextField(blank=True, null=True)),
                (
                    "identifiant_unique",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
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
                ("commentaires", models.TextField(blank=True, null=True)),
                ("cree_le", models.DateTimeField(auto_now_add=True)),
                ("modifie_le", models.DateTimeField(auto_now=True)),
                (
                    "horaires",
                    models.CharField(
                        blank=True,
                        null=True,
                        validators=[qfdmo.models.acteur.validate_opening_hours],
                    ),
                ),
                ("nom", models.CharField(blank=True, max_length=255, null=True)),
                (
                    "acteur_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.acteurtype",
                    ),
                ),
                (
                    "source",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.source",
                    ),
                ),
            ],
            options={
                "verbose_name": "ACTEUR de l'EC - CORRIGÉ",
                "verbose_name_plural": "ACTEURS de l'EC - CORRIGÉ",
            },
        ),
        migrations.AlterModelOptions(
            name="revisionacteur",
            options={
                "verbose_name": "ACTEUR de l'EC - DEPRECATED",
                "verbose_name_plural": "ACTEURS de l'EC - DEPRECATED",
            },
        ),
        migrations.AlterModelOptions(
            name="revisionpropositionservice",
            options={
                "verbose_name": "PROPOSITION DE SERVICE - DEPRECATED",
                "verbose_name_plural": "PROPOSITIONS DE SERVICE - DEPRECATED",
            },
        ),
        migrations.CreateModel(
            name="CorrectionEquipePropositionService",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "acteur_service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.acteurservice",
                    ),
                ),
                (
                    "action",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="qfdmo.action"
                    ),
                ),
                (
                    "revision_acteur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposition_services",
                        to="qfdmo.correctionequipeacteur",
                    ),
                ),
                (
                    "sous_categories",
                    models.ManyToManyField(to="qfdmo.souscategorieobjet"),
                ),
            ],
            options={
                "verbose_name": "PROPOSITION DE SERVICE - CORRIGÉ",
                "verbose_name_plural": "PROPOSITIONS DE SERVICE - CORRIGÉ",
            },
        ),
        migrations.AddConstraint(
            model_name="correctionequipepropositionservice",
            constraint=models.UniqueConstraint(
                fields=("revision_acteur", "action", "acteur_service"),
                name="rps_unique_by_correctionequipeacteur_action_service",
            ),
        ),
    ]
