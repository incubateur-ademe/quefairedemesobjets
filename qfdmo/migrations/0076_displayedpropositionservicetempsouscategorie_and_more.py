# Generated by Django 5.0.4 on 2024-07-08 12:42

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "qfdmo",
            "0075_remove_displayedpropositionservicetemp_sous_categories_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="DisplayedPropositionServiceTempSousCategorie",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                (
                    "proposition_service",
                    models.ForeignKey(
                        db_column="displayedpropositionservice_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.displayedpropositionservicetemp",
                    ),
                ),
                (
                    "sous_categorie_objet",
                    models.ForeignKey(
                        db_column="souscategorieobjet_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="qfdmo.souscategorieobjet",
                    ),
                ),
            ],
            options={
                "db_table": "qfdmo_displayedpropositionservicetemp_sous_categories",
            },
        ),
        migrations.AddField(
            model_name="displayedpropositionservicetemp",
            name="sous_categories",
            field=models.ManyToManyField(
                through="qfdmo.DisplayedPropositionServiceTempSousCategorie",
                to="qfdmo.souscategorieobjet",
            ),
        ),
    ]
