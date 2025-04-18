# Generated by Django 5.1.6 on 2025-04-15 11:49

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    replaces = [
        ("qfdmo", "0140_carteconfig_groupeactionconfig"),
        ("qfdmo", "0141_groupeactionconfig_couleur"),
        ("qfdmo", "0142_alter_groupeactionconfig_unique_together"),
        ("qfdmo", "0143_remove_groupeactionconfig_couleur"),
        ("qfdmo", "0144_alter_groupeactionconfig_groupe_action"),
        ("qfdmo", "0145_merge_20250411_1423"),
        ("qfdmo", "0146_alter_groupeactionconfig_carte_config"),
    ]

    dependencies = [
        ("qfdmo", "0140_drop_views"),
    ]

    operations = [
        migrations.CreateModel(
            name="CarteConfig",
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
                ("nom", models.CharField(unique=True)),
                (
                    "slug",
                    models.SlugField(
                        help_text="Le slug est utilisé pour générer l'url de carte, par exemple: https://quefairedemesobjets.fr/carte/<strong>cyclevia</strong>",
                        unique=True,
                    ),
                ),
                (
                    "groupe_action",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Seules les actions sélectionnées s'afficheront sur la carte\nSi le champ n'est pas renseigné il sera ignoré",
                        to="qfdmo.groupeaction",
                        verbose_name="Groupe d'actions",
                    ),
                ),
                (
                    "source",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Seules les sources sélectionnées s'afficheront sur la carte\nSi le champ n'est pas renseigné il sera ignoré",
                        to="qfdmo.source",
                        verbose_name="Source(s)",
                    ),
                ),
                (
                    "sous_categorie_objet",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Seules les objets sélectionnés s'afficheront sur la carte\nSi le champ n'est pas renseigné il sera ignoré",
                        to="qfdmo.souscategorieobjet",
                        verbose_name="Sous-catégories d'objets filtrés",
                    ),
                ),
            ],
            options={
                "verbose_name": "Carte sur mesure",
                "verbose_name_plural": "Cartes sur mesure",
            },
        ),
        migrations.CreateModel(
            name="GroupeActionConfig",
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
                (
                    "icon",
                    models.FileField(
                        blank=True,
                        help_text="L'icône doit être au format SVG. ",
                        null=True,
                        upload_to="config/groupeaction/icones/",
                        validators=[
                            django.core.validators.FileExtensionValidator(
                                allowed_extensions=["svg"]
                            )
                        ],
                        verbose_name="Supplanter l'icône utilisée pour l'action",
                    ),
                ),
                (
                    "acteur_type",
                    models.ForeignKey(
                        blank=True,
                        help_text="La configuration peut être limitée à un type d'acteur spécifique. Auquel cas il doit être indiqué ici.\nSi aucun type d'acteur n'est renseigné, cette configuration s'appliquera à tout type d'acteur.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.acteurtype",
                        verbose_name="Types d'acteur concernés par la configuration",
                    ),
                ),
                (
                    "carte_config",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="groupe_action_config",
                        to="qfdmo.carteconfig",
                    ),
                ),
                (
                    "groupe_action",
                    models.ForeignKey(
                        blank=True,
                        help_text="La configuration peut être limitée à un groupe d'action spécifique. Auquel cas il doit être indiqué ici.\nSi aucune action n'est renseignée, cette configuration s'appliquera à tout type d'acteur.",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.groupeaction",
                        verbose_name="Groupe d'action",
                    ),
                ),
            ],
            options={
                "unique_together": {("carte_config", "groupe_action", "acteur_type")},
            },
        ),
        migrations.AlterField(
            model_name="groupeactionconfig",
            name="carte_config",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="groupe_action_configs",
                to="qfdmo.carteconfig",
            ),
        ),
    ]
