# Generated by Django 5.1.4 on 2025-01-09 14:04

import django.contrib.gis.db.models.fields
import django.core.validators
import django.db.models.deletion
import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("data", "0001_bancache"),
    ]

    operations = [
        migrations.CreateModel(
            name="SuggestionCohorte",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "identifiant_action",
                    models.CharField(
                        verbose_name="Identifiant de l'action",
                        help_text="(ex : dag_id pour Airflow)",
                    ),
                ),
                (
                    "identifiant_execution",
                    models.CharField(
                        verbose_name="Identifiant de l'execution",
                        help_text="(ex : run_id pour Airflow)",
                    ),
                ),
                (
                    "type_action",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("CLUSTERING", "regroupement/déduplication des acteurs"),
                            (
                                "SOURCE_AJOUT",
                                "ingestion de source de données - nouveau acteur",
                            ),
                            (
                                "SOURCE_MODIFICATION",
                                "ingestion de source de données - modification d'acteur existant",
                            ),
                            ("SOURCE_SUPRESSION", "ingestion de source de données"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("AVALIDER", "À valider"),
                            ("REJETEE", "Rejetée"),
                            ("ATRAITER", "À traiter"),
                            ("ENCOURS", "En cours de traitement"),
                            ("ERREUR", "Fini en erreur"),
                            ("PARTIEL", "Fini avec succès partiel"),
                            ("SUCCES", "Fini avec succès"),
                        ],
                        default="AVALIDER",
                        max_length=50,
                    ),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True,
                        verbose_name="Metadata de la cohorte, données statistiques",
                        null=True,
                    ),
                ),
                (
                    "cree_le",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "modifie_le",
                    models.DateTimeField(
                        auto_now=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Suggestion",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("AVALIDER", "À valider"),
                            ("REJETEE", "Rejetée"),
                            ("ATRAITER", "À traiter"),
                            ("ENCOURS", "En cours de traitement"),
                            ("ERREUR", "Fini en erreur"),
                            ("PARTIEL", "Fini avec succès partiel"),
                            ("SUCCES", "Fini avec succès"),
                        ],
                        default="AVALIDER",
                        max_length=50,
                    ),
                ),
                (
                    "context",
                    models.JSONField(
                        blank=True,
                        verbose_name="Données initiales",
                        null=True,
                    ),
                ),
                (
                    "suggestion",
                    models.JSONField(
                        blank=True, verbose_name="Suggestion de modification"
                    ),
                ),
                (
                    "cree_le",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "modifie_le",
                    models.DateTimeField(
                        auto_now=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
                (
                    "suggestion_cohorte",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="suggestion_unitaires",
                        to="data.suggestioncohorte",
                    ),
                ),
            ],
        ),
    ]
