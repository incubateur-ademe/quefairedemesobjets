# Generated by Django 5.1.8 on 2025-06-05 08:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "qfdmd",
            "0034_synonyme_infotri_squashed_0035_remove_synonyme_infotri_produit_infotri",
        ),
    ]

    operations = [
        migrations.DeleteModel(
            name="CMSPage",
        ),
        migrations.AlterField(
            model_name="produit",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
