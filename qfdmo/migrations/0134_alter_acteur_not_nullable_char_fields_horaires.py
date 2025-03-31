# Generated by Django 5.1.7 on 2025-03-20 21:44

from django.db import migrations, models

import core.validators
import qfdmo.models.acteur


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0133_alter_acteur_not_nullable_char_fields_email"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acteur",
            name="horaires_description",
            field=models.TextField(blank=True, db_default="", default=""),
        ),
        migrations.AlterField(
            model_name="acteur",
            name="horaires_osm",
            field=models.CharField(
                blank=True,
                db_default="",
                default="",
                validators=[qfdmo.models.acteur.validate_opening_hours],
            ),
        ),
        migrations.AlterField(
            model_name="displayedacteur",
            name="horaires_description",
            field=models.TextField(blank=True, db_default="", default=""),
        ),
        migrations.AlterField(
            model_name="displayedacteur",
            name="horaires_osm",
            field=models.CharField(
                blank=True,
                db_default="",
                default="",
                validators=[qfdmo.models.acteur.validate_opening_hours],
            ),
        ),
        migrations.AlterField(
            model_name="displayedacteurtemp",
            name="horaires_description",
            field=models.TextField(blank=True, db_default="", default=""),
        ),
        migrations.AlterField(
            model_name="displayedacteurtemp",
            name="horaires_osm",
            field=models.CharField(
                blank=True,
                db_default="",
                default="",
                validators=[qfdmo.models.acteur.validate_opening_hours],
            ),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="horaires_description",
            field=models.TextField(blank=True, db_default="", default=""),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="horaires_osm",
            field=models.CharField(
                blank=True,
                db_default="",
                default="",
                validators=[qfdmo.models.acteur.validate_opening_hours],
            ),
        ),
    ]
