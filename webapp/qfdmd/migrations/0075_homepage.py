"""
Squashed migration: create HomePage inheriting from ContentPage directly.

Squashes 0075_homepagesettings + 0076_homepage + 0077_delete_homepagesettings
+ 0078_homepage_inherit_contentpage + 0079_remove_homepage_hero_title.

HomePageSettings was created and deleted in the same branch — it is skipped.
HomePage is created directly with contentpage_ptr as the parent link.
hero_title was added then removed in the same branch — it is skipped.
"""

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0074_synonyme_disabled"),
        ("sites_conformes_content_manager", "__latest__"),
        ("wagtailcore", "0096_referenceindex_referenceindex_source_object_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="HomePage",
            fields=[
                (
                    "contentpage_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="sites_conformes_content_manager.contentpage",
                    ),
                ),
                (
                    "hero_subtitle",
                    wagtail.fields.RichTextField(blank=True, verbose_name="Sous-titre"),
                ),
                (
                    "hero_search_label",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Label du champ de recherche",
                    ),
                ),
                (
                    "icons",
                    wagtail.fields.StreamField(
                        [("image", 0)],
                        blank=True,
                        block_lookup={0: ("wagtail.images.blocks.ImageBlock", [], {})},
                        verbose_name="Icônes de la page d'accueil",
                    ),
                ),
            ],
            options={
                "verbose_name": "Page d'accueil",
            },
        ),
    ]
