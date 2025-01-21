from django.core.management import call_command
from django.db import migrations


def delete_parents_without_children(apps, schema_editor):
    call_command("delete_parents_without_children")


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0111_delete_bancache"),
    ]

    operations = [
        migrations.RunPython(delete_parents_without_children),
    ]
