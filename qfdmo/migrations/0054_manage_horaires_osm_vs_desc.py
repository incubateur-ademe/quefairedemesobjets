# Generated by Django 4.2.9 on 2024-03-29 11:14

import opening_hours
from django.db import migrations


def set_horaires(apps, schema_editor):
    Acteur = apps.get_model("qfdmo", "Acteur")
    RevisionActeur = apps.get_model("qfdmo", "RevisionActeur")

    for a in Acteur.objects.exclude(horaires_osm__isnull=True).exclude(horaires_osm=""):
        if not opening_hours.validate(a.horaires_osm):
            a.horaires_description = a.horaires_osm
            a.horaires_osm = ""
            a.save()

    for a in RevisionActeur.objects.exclude(horaires_osm__isnull=True).exclude(
        horaires_osm=""
    ):
        if not opening_hours.validate(a.horaires_osm):
            a.horaires_description = a.horaires_osm
            a.horaires_osm = ""
            a.save()


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0053_rename_horaires_acteur_horaires_osm_and_more"),
    ]

    operations = [
        migrations.RunPython(set_horaires, migrations.RunPython.noop),
    ]
