# Generated by Django 5.0.4 on 2024-07-15 15:03

from django.db import migrations, models


def set_null_existing_fields(apps, schema_editor):
    Acteur = apps.get_model("qfdmo", "Acteur")
    RevisionActeur = apps.get_model("qfdmo", "RevisionActeur")
    Acteur.objects.all().update(
        exclusivite_de_reprisereparation=None, uniquement_sur_rdv=None
    )
    RevisionActeur.objects.all().update(
        exclusivite_de_reprisereparation=None, uniquement_sur_rdv=None
    )


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0081_alter_acteur_exclusivite_de_reprisereparation_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acteur",
            name="exclusivite_de_reprisereparation",
            field=models.BooleanField(
                null=True, verbose_name="Exclusivité de reprise/réparation"
            ),
        ),
        migrations.AlterField(
            model_name="acteur",
            name="uniquement_sur_rdv",
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name="displayedacteur",
            name="exclusivite_de_reprisereparation",
            field=models.BooleanField(
                null=True, verbose_name="Exclusivité de reprise/réparation"
            ),
        ),
        migrations.AlterField(
            model_name="displayedacteur",
            name="uniquement_sur_rdv",
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name="displayedacteurtemp",
            name="exclusivite_de_reprisereparation",
            field=models.BooleanField(
                null=True, verbose_name="Exclusivité de reprise/réparation"
            ),
        ),
        migrations.AlterField(
            model_name="displayedacteurtemp",
            name="uniquement_sur_rdv",
            field=models.BooleanField(null=True),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="exclusivite_de_reprisereparation",
            field=models.BooleanField(
                null=True, verbose_name="Exclusivité de reprise/réparation"
            ),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="uniquement_sur_rdv",
            field=models.BooleanField(null=True),
        ),
        migrations.RunPython(set_null_existing_fields, migrations.RunPython.noop),
    ]