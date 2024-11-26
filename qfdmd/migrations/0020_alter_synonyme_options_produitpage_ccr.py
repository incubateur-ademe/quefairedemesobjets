# Generated by Django 5.1.1 on 2024-11-26 14:50

import wagtail.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0019_rename_content_elementreutilisable_contenu_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="synonyme",
            options={"ordering": ("nom",)},
        ),
        migrations.AddField(
            model_name="produitpage",
            name="ccr",
            field=wagtail.fields.StreamField(
                [
                    ("element_reutilisable", 0),
                    ("rich_text", 1),
                    ("heading", 2),
                    ("carte", 4),
                ],
                block_lookup={
                    0: (
                        "wagtail.snippets.blocks.SnippetChooserBlock",
                        ("qfdmd.elementreutilisable",),
                        {},
                    ),
                    1: ("wagtail.blocks.RichTextBlock", (), {}),
                    2: ("wagtail.blocks.CharBlock", (), {}),
                    3: (
                        "wagtail.blocks.MultipleChoiceBlock",
                        [],
                        {
                            "choices": [
                                ("reparer", "Reparer"),
                                ("donner", "Donner"),
                                ("preter", "Prêter"),
                                ("acheter", "Acheter"),
                            ]
                        },
                    ),
                    4: ("wagtail.blocks.StructBlock", [[("gestes", 3)]], {}),
                },
                default=dict,
                verbose_name="Bon état",
            ),
            preserve_default=False,
        ),
    ]
