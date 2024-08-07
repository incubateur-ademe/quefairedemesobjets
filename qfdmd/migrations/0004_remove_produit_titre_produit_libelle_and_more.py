# Generated by Django 5.0.4 on 2024-07-04 07:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0003_alter_produit_options"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="produit",
            name="titre",
        ),
        migrations.AddField(
            model_name="produit",
            name="libelle",
            field=models.CharField(
                blank=True,
                help_text="Ce champ est facultatif et n'est utilisé que dans l'administration Django.",
                unique=True,
                verbose_name="Libellé",
            ),
        ),
        migrations.AlterField(
            model_name="produit",
            name="id",
            field=models.IntegerField(
                help_text="Correspond à l'identifiant ID défini dans les données <i>Que Faire</i>.",
                primary_key=True,
                serialize=False,
            ),
        ),
    ]
