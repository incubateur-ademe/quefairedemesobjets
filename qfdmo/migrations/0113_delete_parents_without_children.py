from django.core.management import call_command
from django.db import migrations


def delete_parents_without_children(apps, schema_editor):
    call_command("delete_parents_without_children")


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0112_correction_source_codes_lvao"),
    ]

    operations = [
        migrations.RunPython(delete_parents_without_children),
    ]
