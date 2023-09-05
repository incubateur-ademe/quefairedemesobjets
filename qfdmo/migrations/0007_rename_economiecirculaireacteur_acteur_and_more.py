# Generated by Django 4.2.4 on 2023-09-05 14:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("qfdmo", "0006_rename_reemploiacteur_economiecirculaireacteur_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="EconomieCirculaireActeur",
            new_name="Acteur",
        ),
        migrations.RemoveConstraint(
            model_name="propositionservice",
            name="unique_by_acteur_action_service",
        ),
        migrations.RenameField(
            model_name="propositionservice",
            old_name="economie_circulaire_acteur",
            new_name="acteur",
        ),
        migrations.AddConstraint(
            model_name="propositionservice",
            constraint=models.UniqueConstraint(
                fields=("acteur", "action", "acteur_service"),
                name="unique_by_acteur_action_service",
            ),
        ),
    ]
