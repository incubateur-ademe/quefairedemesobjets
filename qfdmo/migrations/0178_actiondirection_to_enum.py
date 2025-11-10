from django.contrib.postgres.fields import ArrayField
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0177_rename_label_carteconfig_label_qualite_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="action",
            name="direction_codes",
            field=ArrayField(
                base_field=models.CharField(
                    choices=[
                        ("jai", "J'ai un objet"),
                        ("jecherche", "Je recherche un objet"),
                    ],
                    max_length=32,
                ),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AddField(
            model_name="carteconfig",
            name="direction_codes",
            field=ArrayField(
                base_field=models.CharField(
                    choices=[
                        ("jai", "J'ai un objet"),
                        ("jecherche", "Je recherche un objet"),
                    ],
                    max_length=32,
                ),
                blank=True,
                default=list,
                help_text="Seules les actions correspondantes à la direction choisie "
                "s'afficheront sur la carte\nSi le champ n'est pas renseigné il sera ignoré",
                size=None,
                verbose_name="Direction des actions",
            ),
        ),
    ]
