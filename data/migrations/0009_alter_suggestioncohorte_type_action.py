# Generated by Django 5.1.7 on 2025-03-20 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0008_alter_suggestioncohorte_type_action"),
    ]

    operations = [
        migrations.AlterField(
            model_name="suggestioncohorte",
            name="type_action",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CRAWL_URLS", "🔗 URLs scannées"),
                    ("RGPD_ANONYMISATION", "🕵️ Anonymisation RGPD"),
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
