# Generated by Django 5.1.1 on 2024-12-04 13:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0016_alter_produit_comment_les_eviter"),
    ]

    operations = [
        migrations.AddField(
            model_name="synonyme",
            name="pin_on_homepage",
            field=models.BooleanField(default=False),
        ),
    ]
