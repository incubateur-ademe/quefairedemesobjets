# Generated by Django 5.1.1 on 2024-11-05 13:52

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0106_remove_action_couleur_claire"),
    ]

    operations = [
        migrations.AlterField(
            model_name="action",
            name="couleur",
            field=colorfield.fields.ColorField(
                blank=True,
                choices=[
                    ("#AEA397", "beige-gris-galet"),
                    ("#3558A2", "blue-cumulus-sun-368"),
                    ("#417DC4", "blue-cumulus"),
                    ("#bfccfb", "blue-ecume-850"),
                    ("#465F9D", "blue-ecume"),
                    ("#0055FF", "blue-france"),
                    ("#D1B781", "brown-cafe-creme-main-782"),
                    ("#D1B781", "brown-cafe-creme"),
                    ("#C08C65", "brown-caramel"),
                    ("#BD987A", "brown-opera"),
                    ("#009099", "green-archipel"),
                    ("#95e257", "green-bourgeon-850"),
                    ("#68A532", "green-bourgeon"),
                    ("#00A95F", "green-emeraude"),
                    ("#73e0cf", "green-menthe-850"),
                    ("#009081", "green-menthe-main-548"),
                    ("#37635f", "green-menthe-sun-373"),
                    ("#009081", "green-menthe"),
                    ("#B7A73F", "green-tilleul-verveine"),
                    ("#E4794A", "orange-terre-battue-main-645"),
                    ("#E4794A", "orange-terre-battue"),
                    ("#E18B76", "pink-macaron"),
                    ("#fcbfb7", "pink-tuile-850"),
                    ("#CE614A", "pink-tuile"),
                    ("#A558A0", "purple-glycine-main-494"),
                    ("#A558A0", "purple-glycine"),
                    ("#fcc63a", "yellow-moutarde-850"),
                    ("#C3992A", "yellow-moutarde"),
                    ("#e9c53b", "yellow-tournesol"),
                    ("#bb8568", "brown-caramel-sun-425-hover"),
                    ("#FEF3FD", "purple-glycine-975"),
                    ("#A558A0", "purple-glycine-main-494"),
                    ("#F3F6FE", "blue-cumulus-975"),
                    ("#417DC4", "blue-cumulus-main-526"),
                    ("#D1B781", "brown-cafe-creme-main-78"),
                    ("#F7ECDB", "brown-cafe-creme-950"),
                    ("#009081", "green-menthe-main-548"),
                    ("#DFFDF7", "green-menthe-975"),
                    ("#CE614A", "pink-tuile-main-556"),
                    ("#FEF4F3", "pink-tuile-975"),
                ],
                default="#C3992A",
                help_text="Cette couleur est utilisée uniquement pour la version formulaire (épargnons).",
                image_field=None,
                max_length=255,
                null=True,
                samples=None,
            ),
        ),
    ]
