# Generated migration for SearchTerm base model

import modelsearch.index
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SearchTerm",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
            ],
            options={
                "verbose_name": "Terme de recherche",
                "verbose_name_plural": "Termes de recherche",
            },
            bases=(modelsearch.index.Indexed, models.Model),
        ),
    ]
