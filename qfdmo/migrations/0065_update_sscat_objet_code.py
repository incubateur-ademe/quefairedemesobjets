# Generated by Django 4.2.9 on 2024-04-05 07:16

from django.db import migrations
from unidecode import unidecode


def set_code(apps, schema_editor):
    CategorieObjet = apps.get_model("qfdmo", "CategorieObjet")
    SousCategorieObjet = apps.get_model("qfdmo", "SousCategorieObjet")
    Objet = apps.get_model("qfdmo", "Objet")
    for cat in CategorieObjet.objects.all():
        cat.code = unidecode(cat.libelle)
        cat.save()
    for sscat in SousCategorieObjet.objects.all():
        sscat.code = unidecode(sscat.libelle)
        sscat.save()
    for obj in Objet.objects.all():
        obj.code = unidecode(obj.libelle)
        obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0064_alter_souscategorieobjet_options_and_more"),
    ]

    operations = [
        migrations.RunPython(set_code, migrations.RunPython.noop),
    ]
