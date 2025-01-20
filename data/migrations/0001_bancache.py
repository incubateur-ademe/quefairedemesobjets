# Generated by Django 5.1.4 on 2025-01-09 14:04

import django.contrib.gis.db.models.fields
import django.core.validators
import django.db.models.deletion
import django.db.models.functions.datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="BANCache",
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
                ("adresse", models.CharField(blank=True, null=True)),
                (
                    "code_postal",
                    models.CharField(blank=True, null=True),
                ),
                ("ville", models.CharField(blank=True, null=True)),
                (
                    "location",
                    django.contrib.gis.db.models.fields.PointField(
                        blank=True, null=True, srid=4326
                    ),
                ),
                ("ban_returned", models.JSONField(blank=True, null=True)),
                (
                    "modifie_le",
                    models.DateTimeField(
                        auto_now=True,
                        db_default=django.db.models.functions.datetime.Now(),
                    ),
                ),
            ],
            options={
                "verbose_name": "Cache BAN",
                "verbose_name_plural": "Cache BAN",
            },
        ),
    ]
