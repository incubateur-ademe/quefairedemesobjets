# Generated by Django 5.1.6 on 2025-04-10 15:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0143_remove_groupeactionconfig_couleur"),
    ]

    operations = [
        migrations.AlterField(
            model_name="groupeactionconfig",
            name="groupe_action",
            field=models.ForeignKey(
                blank=True,
                help_text="La configuration peut être limitée à un groupe d'action spécifique. Auquel cas il doit être indiqué ici.\nSi aucune action n'est renseignée, cette configuration s'appliquera à tout type d'acteur.",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="qfdmo.groupeaction",
                verbose_name="Groupe d'action",
            ),
        ),
    ]
