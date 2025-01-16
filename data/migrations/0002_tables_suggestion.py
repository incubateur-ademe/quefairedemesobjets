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
                        help_text="Identifiant de l'action (ex : dag_id pour Airflow)",
                        max_length=250,
                    ),
                ),
                (
                    "identifiant_execution",
                    models.CharField(
                        help_text="Identifiant de l'execution (ex : run_id pour Airflow)",
                        max_length=250,
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
                                "SOURCE_MISESAJOUR",
                                "ingestion de source de données - modification d'acteur existant",
                            ),
                            ("SOURCE_SUPRESSION", "ingestion de source de données"),
                        ],
                        max_length=250,
                    ),
                ),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("AVALIDER", "À valider"),
                            ("REJETER", "Rejeter"),
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
                        help_text="Metadata de la cohorte, données statistiques",
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
            name="SuggestionUnitaire",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "statut",
                    models.CharField(
                        choices=[
                            ("AVALIDER", "À valider"),
                            ("REJETER", "Rejeter"),
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
                        help_text="Contexte de la suggestion : données initiales",
                        null=True,
                    ),
                ),
                (
                    "suggestion",
                    models.JSONField(
                        blank=True, help_text="Suggestion de modification"
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
