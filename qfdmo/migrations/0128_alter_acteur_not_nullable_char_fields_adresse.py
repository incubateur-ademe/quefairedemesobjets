# Generated by Django 5.1.7 on 2025-03-20 21:44

from django.db import migrations, models

import core.validators
import qfdmo.models.acteur


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0127_add_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acteur",
            name="adresse",
            field=models.CharField(
                blank=True, db_default="", default="", max_length=255
            ),
        ),
        migrations.AlterField(
            model_name="displayedacteur",
            name="adresse",
            field=models.CharField(
                blank=True, db_default="", default="", max_length=255
            ),
        ),
        migrations.AlterField(
            model_name="displayedacteurtemp",
            name="adresse",
            field=models.CharField(
                blank=True, db_default="", default="", max_length=255
            ),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="adresse",
            field=models.CharField(
                blank=True, db_default="", default="", max_length=255
            ),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="adresse_complement",
            field=models.CharField(
                blank=True, db_default="", default="", max_length=255
            ),
        ),
    ]
