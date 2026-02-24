"""
Migrate HomePage to inherit from ContentPage (sites_conformes) instead of Page directly.

Schema changes:
  - qfdmd_homepage: drop page_ptr_id + body, add contentpage_ptr_id
  - sites_conformes_content_manager_contentpage: insert a row for every existing HomePage

For fresh environments (staging/production) the qfdmd_homepage table is empty so only
the schema change matters.  For local dev DBs that already have a HomePage row the
RunSQL operations create the intermediate contentpage row first.
"""

import django.db.models.deletion
from django.db import migrations, models


def create_contentpage_rows(apps, schema_editor):
    """
    For each existing HomePage row, insert the required parent-table rows so that
    the new contentpage_ptr FK can be satisfied, then populate contentpage_ptr_id.
    """
    schema_editor.execute(
        """
        INSERT INTO sites_conformes_content_manager_contentpage
            (page_ptr_id, body, header_color_class, header_darken, header_image_id,
             header_large, header_with_title, header_cta_text, header_cta_buttons,
             source_url, preview_image_id, hero)
        SELECT
            page_ptr_id,
            '[]',   -- body
            NULL,   -- header_color_class
            FALSE,  -- header_darken
            NULL,   -- header_image_id
            FALSE,  -- header_large
            FALSE,  -- header_with_title
            '',     -- header_cta_text
            '[]',   -- header_cta_buttons
            NULL,   -- source_url
            NULL,   -- preview_image_id
            '[]'    -- hero
        FROM qfdmd_homepage
        WHERE page_ptr_id NOT IN (
            SELECT page_ptr_id FROM sites_conformes_content_manager_contentpage
        )
        """,
    )
    # Now populate the nullable contentpage_ptr_id column from the old page_ptr_id
    schema_editor.execute(
        """
        UPDATE qfdmd_homepage
        SET contentpage_ptr_id = page_ptr_id
        WHERE contentpage_ptr_id IS NULL
        """,
    )


def delete_contentpage_rows(apps, schema_editor):
    """Reverse: remove the contentpage rows that were created for HomePage."""
    schema_editor.execute(
        """
        DELETE FROM sites_conformes_content_manager_contentpage
        WHERE page_ptr_id IN (SELECT page_ptr_id FROM qfdmd_homepage)
        """,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0077_delete_homepagesettings"),
        ("sites_conformes_content_manager", "__latest__"),
    ]

    operations = [
        # 1. Add contentpage_ptr as nullable first so we can populate it before enforcing NOT NULL.
        migrations.AddField(
            model_name="homepage",
            name="contentpage_ptr",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                to="sites_conformes_content_manager.contentpage",
            ),
        ),
        # 2. Populate intermediate contentpage rows and fill contentpage_ptr_id.
        migrations.RunPython(
            create_contentpage_rows, reverse_code=delete_contentpage_rows
        ),
        # 3. Drop the old page_ptr OneToOneField (and its underlying column page_ptr_id).
        migrations.RemoveField(
            model_name="homepage",
            name="page_ptr",
        ),
        # 4. Drop the body StreamField (now inherited from SitesFacilesBasePage / ContentPage).
        migrations.RemoveField(
            model_name="homepage",
            name="body",
        ),
        # 5. Make contentpage_ptr NOT NULL and the primary key now that it's populated.
        migrations.AlterField(
            model_name="homepage",
            name="contentpage_ptr",
            field=models.OneToOneField(
                auto_created=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                serialize=False,
                to="sites_conformes_content_manager.contentpage",
            ),
        ),
    ]
