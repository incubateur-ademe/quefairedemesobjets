# Generated by Django 5.1.1 on 2024-10-10 15:27

from django.db import migrations, models

from qfdmo.validators import CodeValidator

mapping = {
    "ess": "ess",
    "déchèterie": "decheterie",
    "établissement de santé": "ets_sante",
    "point d'apport volontaire privé": "pav_prive",
    "point d'apport volontaire public": "pav_public",
    "acteur digital": "acteur_digital",
    "commerce": "commerce",
    "artisan": "artisan",
    "collectivité": "collectivite",
    "plateforme inertes": "plateforme_inertes",
    "point d'apport volontaire ponctuel": "pav_ponctuel",
}


def update_acteurtype_code(apps, schema_editor):
    ActeurType = apps.get_model("qfdmo", "ActeurType")
    for code, new_code in mapping.items():
        ActeurType.objects.filter(code=code).update(code=new_code)


def rollcack_acteurtype_code(apps, schema_editor):
    ActeurType = apps.get_model("qfdmo", "ActeurType")
    for code, new_code in mapping.items():
        ActeurType.objects.filter(code=new_code).update(code=code)


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0094_dagrunchange_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acteurtype",
            name="code",
            field=models.CharField(
                help_text=(
                    "Ce champ est utilisé lors de l'import de données, il ne doit pas"
                    " être mis à jour sous peine de casser l'import de données"
                ),
                max_length=255,
                unique=True,
                validators=[CodeValidator()],
            ),
        ),
        migrations.RunPython(update_acteurtype_code, rollcack_acteurtype_code),
    ]