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
                (
                    "search_variants",
                    models.TextField(
                        blank=True,
                        default="",
                        help_text=(
                            "Termes alternatifs permettant de trouver cette page "
                            "dans la recherche. Ces variantes sont invisibles pour "
                            "les utilisateurs mais améliorent la recherche. Séparez "
                            "les termes par des virgules ou des retours à la ligne."
                        ),
                        verbose_name="Variantes de recherche",
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
