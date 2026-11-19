from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0192_groupe_action_libelle_court"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="souscategorieobjet",
            name="afficher",
        ),
        migrations.RemoveField(
            model_name="souscategorieobjet",
            name="afficher_carte",
        ),
    ]
