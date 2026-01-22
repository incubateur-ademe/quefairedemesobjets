# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0069_delete_suggestion"),
    ]

    operations = [
        migrations.AddField(
            model_name="produitpage",
            name="est_famille",
            field=models.BooleanField(
                default=False,
                help_text="Si coché, cette page sera affichée avec le template "
                "famille (fond vert) et pourra contenir des sous-produits.",
                verbose_name="Est une famille",
            ),
        ),
    ]
