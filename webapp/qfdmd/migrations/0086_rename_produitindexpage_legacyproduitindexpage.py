from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0085_add_break_block_to_streamfield"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="ProduitIndexPage",
            new_name="LegacyProduitIndexPage",
        ),
        migrations.AlterModelOptions(
            name="legacyproduitindexpage",
            options={"verbose_name": "Index des familles & produits (legacy)"},
        ),
    ]
