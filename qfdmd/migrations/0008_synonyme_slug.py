# Generated by Django 5.1.1 on 2024-11-13 16:36

import django_extensions.db.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0007_synomyne"),
    ]

    operations = [
        migrations.AddField(
            model_name="synonyme",
            name="slug",
            field=django_extensions.db.fields.AutoSlugField(
                blank=True, editable=False, populate_from=["nom"]
            ),
        ),
    ]
