# Generated by Django 5.1.6 on 2025-04-24 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0011_alter_suggestioncohorte_type_action"),
    ]

    operations = [
        migrations.AlterField(
            model_name="suggestioncohorte",
            name="type_action",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CRAWL_URLS", "🔗 URLs scannées"),
                    ("ENRICH_ACTEURS_CLOSED", "🚪 Acteurs fermés"),
                    ("ENRICH_ACTEURS_RGPD", "🕵 Anonymisation RGPD"),
                    ("CLUSTERING", "regroupement/déduplication des acteurs"),
                    ("SOURCE_AJOUT", "ingestion de source de données - nouveau acteur"),
                    (
                        "SOURCE_MODIFICATION",
                        "ingestion de source de données - modification d'acteur existant",
                    ),
                    ("SOURCE_SUPRESSION", "ingestion de source de données"),
                ],
                max_length=50,
            ),
        ),
    ]
