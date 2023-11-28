# Generated by Django 4.2.7 on 2023-11-28 17:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("qfdmo", "0034_directions_actions_related_name"),
    ]

    operations = [
        migrations.AlterField(
            model_name="correctionacteur",
            name="final_acteur",
            field=models.ForeignKey(
                db_constraint=False,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                related_name="corrections",
                to="qfdmo.finalacteur",
            ),
        ),
    ]
