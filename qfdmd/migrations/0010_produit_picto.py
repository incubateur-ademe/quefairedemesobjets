# Generated by Django 5.1.1 on 2024-11-20 16:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0009_auto_20241120_1443"),
    ]

    operations = [
        migrations.AddField(
            model_name="produit",
            name="picto",
            field=models.ImageField(blank=True, null=True, upload_to="pictos"),
        ),
    ]