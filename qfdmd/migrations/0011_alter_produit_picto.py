# Generated by Django 5.1.1 on 2024-11-20 16:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0010_produit_picto"),
    ]

    operations = [
        migrations.AlterField(
            model_name="produit",
            name="picto",
            field=models.FileField(blank=True, null=True, upload_to="pictos"),
        ),
    ]
