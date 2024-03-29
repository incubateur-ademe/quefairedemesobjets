# Generated by Django 4.2.9 on 2024-02-28 10:11

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models

import qfdmo.models.acteur


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0041_correctionequipeacteur_alter_revisionacteur_options_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DisplayedActeurTemp",
            fields=[
                ("nom", models.CharField(max_length=255)),
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
                (
                    "acteur_type",
                    models.ForeignKey(
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
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="DisplayedPropositionServiceTemp",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "acteur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposition_services",
                        to="qfdmo.displayedacteurtemp",
                    ),
                ),
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
                    "sous_categories",
                    models.ManyToManyField(to="qfdmo.souscategorieobjet"),
                ),
            ],
        ),
    ]
