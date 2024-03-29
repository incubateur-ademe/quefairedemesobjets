# Generated by Django 4.2.9 on 2024-03-29 11:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0052_dagrun"),
    ]

    operations = [
        migrations.RenameField(
            model_name="acteur",
            old_name="horaires",
            new_name="horaires_osm",
        ),
        migrations.RenameField(
            model_name="displayedacteur",
            old_name="horaires",
            new_name="horaires_osm",
        ),
        migrations.RenameField(
            model_name="displayedacteurtemp",
            old_name="horaires",
            new_name="horaires_osm",
        ),
        migrations.RenameField(
            model_name="revisionacteur",
            old_name="horaires",
            new_name="horaires_osm",
        ),
        migrations.AddField(
            model_name="acteur",
            name="horaires_description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="displayedacteur",
            name="horaires_description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="displayedacteurtemp",
            name="horaires_description",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="revisionacteur",
            name="horaires_description",
            field=models.TextField(blank=True, null=True),
        ),
    ]
