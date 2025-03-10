# Generated by Django 4.2.4 on 2023-08-11 09:35

import django.contrib.gis.db.models.fields
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("qfdmo", "0004_acteurservice_actions"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReemploiActeur",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("nom", models.CharField(max_length=255)),
                (
                    "identifiant_unique",
                    models.CharField(
                        blank=True, max_length=255, null=True, unique=True
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
                ("location", django.contrib.gis.db.models.fields.PointField(srid=4326)),
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
                    "source_donnee",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "identifiant_externe",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "acteur_type",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.acteurtype",
                    ),
                ),
            ],
            options={
                "verbose_name": "Acteur du Réemploi",
                "verbose_name_plural": "Acteurs du Réemploi",
            },
        ),
        migrations.CreateModel(
            name="PropositionService",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "acteur_service",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposition_services",
                        to="qfdmo.acteurservice",
                    ),
                ),
                (
                    "action",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposition_services",
                        to="qfdmo.action",
                    ),
                ),
                (
                    "reemploi_acteur",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposition_services",
                        to="qfdmo.reemploiacteur",
                    ),
                ),
                (
                    "sous_categories",
                    models.ManyToManyField(
                        related_name="proposition_services",
                        to="qfdmo.souscategorieobjet",
                    ),
                ),
            ],
            options={
                "verbose_name": "Proposition de service",
                "verbose_name_plural": "Proposition de service",
            },
        ),
        migrations.AddConstraint(
            model_name="propositionservice",
            constraint=models.UniqueConstraint(
                fields=("reemploi_acteur", "action", "acteur_service"),
                name="unique_by_acteur_action_service",
            ),
        ),
    ]
