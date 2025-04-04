# Generated by Django 5.1.1 on 2024-10-12 07:55

from django.core.management import call_command
from django.db import migrations


def update_screlec_to_batribox(apps, schema_editor):
    call_command(
        "source_code_modification",
        old_source_code="screlec",
        new_source_code="batribox",
    )


def update_batribox_to_screlec(apps, schema_editor):
    call_command(
        "source_code_modification",
        old_source_code="batribox",
        new_source_code="screlec",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0115_acteur_models_code_constraint"),
    ]

    operations = [
        migrations.RunPython(update_screlec_to_batribox, update_batribox_to_screlec),
    ]
