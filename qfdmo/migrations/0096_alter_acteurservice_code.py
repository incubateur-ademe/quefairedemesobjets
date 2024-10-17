# Generated by Django 5.1.1 on 2024-10-10 16:22

from django.db import migrations, models

from qfdmo.validators import CodeValidator

mapping = {
    "Location entre particuliers": "localtion_particuliers",
    "Location par un professionnel": "location_professionnel",
    "Echanges entre particuliers": "echanges_particuliers",
    "Don entre particuliers": "don_particuliers",
    "Achat, revente par un professionnel": "achat_revente_professionnel",
    "Achat, revente entre particuliers": "achat_revente_particuliers",
    "Depôt-vente": "depot_vente",
    "Pièces détachées": "pieces_detachees",
    "Service de réparation": "service_de_reparation",
    "Tutoriels et diagnostics en ligne": "tutoriels_et_diagnostics_en_ligne",
    "Recyclerie": "recyclerie",
    "Atelier pour réparer soi-même": "atelier_pour_reparer_soi_meme",
    "Espace de partage": "espace_de_partage",
    "Relai d'acteurs et d'événements": "relai_acteurs_et_evenements",
    "Collecte par une structure spécialisée": "structure_de_collecte",
    "Structure qui va sous-traiter la réparation": "structure_qui_sous_traite_la_reparation",
    "Partage entre particuliers": "partage_particuliers",
}


def update_acteurservice_code(apps, schema_editor):
    ActeurService = apps.get_model("qfdmo", "ActeurService")
    for code, new_code in mapping.items():
        ActeurService.objects.filter(code=code).update(code=new_code)


def rollcack_acteurservice_code(apps, schema_editor):
    ActeurService = apps.get_model("qfdmo", "ActeurService")
    for code, new_code in mapping.items():
        ActeurService.objects.filter(code=new_code).update(code=code)


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0095_alter_acteurtype_code"),
    ]

    operations = [
        migrations.AlterField(
            model_name="acteurservice",
            name="code",
            field=models.CharField(
                help_text=(
                    "Ce champ est utilisé lors de l'import de données, il ne doit"
                    " pas être mis à jour sous peine de casser l'import de données"
                ),
                max_length=255,
                unique=True,
                validators=[CodeValidator()],
            ),
        ),
        migrations.RunPython(update_acteurservice_code, rollcack_acteurservice_code),
    ]
