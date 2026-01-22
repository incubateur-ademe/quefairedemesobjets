from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("search", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="searchterm",
            old_name="content_type",
            new_name="linked_content_type",
        ),
        migrations.RenameField(
            model_name="searchterm",
            old_name="object_id",
            new_name="linked_object_id",
        ),
        migrations.RenameIndex(
            model_name="searchterm",
            old_name="search_sear_content_43e25e_idx",
            new_name="search_sear_linked__a1b2c3_idx",
        ),
        migrations.AlterUniqueTogether(
            name="searchterm",
            unique_together={("linked_content_type", "linked_object_id")},
        ),
    ]
