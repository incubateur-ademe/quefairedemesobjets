# Generated by Django 5.1.1 on 2024-11-28 13:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0107_alter_source_licence"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="lvaobaserevision",
            name="lvao_base",
        ),
        migrations.RemoveField(
            model_name="lvaobaserevision",
            name="acteur_services",
        ),
        migrations.RemoveField(
            model_name="lvaobaserevision",
            name="acteur_type",
        ),
        migrations.RemoveField(
            model_name="lvaobaserevision",
            name="actions",
        ),
        migrations.RemoveField(
            model_name="lvaobaserevision",
            name="sous_categories",
        ),
        migrations.DeleteModel(
            name="LVAOBase",
        ),
        migrations.DeleteModel(
            name="LVAOBaseRevision",
        ),
    ]
