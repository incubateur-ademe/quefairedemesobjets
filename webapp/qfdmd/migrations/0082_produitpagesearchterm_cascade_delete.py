import django.db.models.deletion
from django.db import migrations, models


def delete_orphaned_search_terms(apps, schema_editor):
    ProduitPageSearchTerm = apps.get_model("qfdmd", "ProduitPageSearchTerm")
    ProduitPageSearchTerm.objects.filter(produit_page__isnull=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0081_homepage"),
    ]

    operations = [
        migrations.RunPython(
            delete_orphaned_search_terms,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="produitpagesearchterm",
            name="produit_page",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="produit_page_search_term",
                to="qfdmd.produitpage",
            ),
        ),
    ]
