# Generated by Django 5.1.5 on 2025-02-13 16:51

import django.db.models.deletion
from django.db import migrations, models

import qfdmo.models.acteur


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmo", "0122_alter_revisionacteur_email"),
    ]

    operations = [
        migrations.CreateModel(
            name="RevisionActeurParent",
            fields=[],
            options={
                "verbose_name": "Parent",
                "verbose_name_plural": "Parents",
                "proxy": True,
                "indexes": [],
                "constraints": [],
            },
            bases=("qfdmo.revisionacteur",),
        ),
        migrations.AlterField(
            model_name="revisionacteur",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                help_text="RevisionActeur «chapeau» utilisé pour dédupliquer cet acteur",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="duplicats",
                to="qfdmo.revisionacteurparent",
                validators=[qfdmo.models.acteur.clean_parent],
                verbose_name="Dédupliqué par",
            ),
        ),
    ]
