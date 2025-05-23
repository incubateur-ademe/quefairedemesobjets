# Generated by Django 5.1.1 on 2024-11-07 17:14

from django.db import migrations


def rename_cma_source_code(apps, schema_editor):
    Source = apps.get_model("qfdmo", "Source")
    Source.objects.filter(code="CMA - Chambre des métiers et de l'artisanat").update(
        code="cma_reparacteur"
    )


def reverse_rename_cma_source_code(apps, schema_editor):
    Source = apps.get_model("qfdmo", "Source")
    Source.objects.filter(code="cma_reparacteur").update(
        code="CMA - Chambre des métiers et de l'artisanat"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0099_cma_source_update"),
    ]

    operations = [
        migrations.RunPython(
            rename_cma_source_code,
            reverse_rename_cma_source_code,
        ),
    ]
