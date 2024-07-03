# Generated by Django 5.0.4 on 2024-07-03 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Produit",
            fields=[
                ("titre", models.CharField(unique=True)),
                ("id", models.IntegerField(primary_key=True, serialize=False)),
                (
                    "sous_categories",
                    models.ManyToManyField(
                        related_name="qfdmd_produits", to="qfdmo.souscategorieobjet"
                    ),
                ),
            ],
            options={
                "verbose_name": "Produit",
            },
        ),
    ]
