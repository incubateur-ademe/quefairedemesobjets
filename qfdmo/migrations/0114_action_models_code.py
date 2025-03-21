# Generated by Django 5.1.4 on 2025-01-23 10:08

from django.db import migrations, models

import qfdmo.validators


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0113_delete_parents_without_children"),
    ]

    operations = [
        migrations.AlterField(
            model_name="action",
            name="code",
            field=models.CharField(
                max_length=255,
                unique=True,
                validators=[qfdmo.validators.CodeValidator()],
            ),
        ),
        migrations.AlterField(
            model_name="actiondirection",
            name="code",
            field=models.CharField(
                max_length=255,
                unique=True,
                validators=[qfdmo.validators.CodeValidator()],
            ),
        ),
        migrations.AlterField(
            model_name="groupeaction",
            name="code",
            field=models.CharField(
                max_length=255,
                unique=True,
                validators=[qfdmo.validators.CodeValidator()],
            ),
        ),
        migrations.AddConstraint(
            model_name="action",
            constraint=models.CheckConstraint(
                condition=models.Q(("code__regex", "^[0-9a-z_]+$")),
                name="action_code_format",
            ),
        ),
        migrations.AddConstraint(
            model_name="actiondirection",
            constraint=models.CheckConstraint(
                condition=models.Q(("code__regex", "^[0-9a-z_]+$")),
                name="action_direction_code_format",
            ),
        ),
        migrations.AddConstraint(
            model_name="groupeaction",
            constraint=models.CheckConstraint(
                condition=models.Q(("code__regex", "^[0-9a-z_]+$")),
                name="groupe_action_code_format",
            ),
        ),
    ]
