# Generated by Django 5.0.4 on 2024-07-03 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0073_alter_action_and_groupeaction"),
    ]

    operations = [
        migrations.AddField(
            model_name="souscategorieobjet",
            name="qfdmd_afficher_carte",
            field=models.BooleanField(
                default=False,
                help_text="afficher la carte LVAO dans les fiches produits “Que faire de mes objets et déchets” avec les identifiants indiqués au niveau de la sous-catégorie",
                verbose_name="Afficher la carte dans l’assistant",
            ),
        ),
    ]
