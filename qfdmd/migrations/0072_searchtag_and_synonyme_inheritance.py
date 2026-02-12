import django.db.models.deletion
import modelcluster.contrib.taggit
import modelcluster.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0071_remove_produitpage_bonus_and_more"),
        ("search", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SearchTag",
            fields=[
                (
                    "searchterm_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="search.searchterm",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, unique=True, verbose_name="name"),
                ),
                (
                    "slug",
                    models.SlugField(
                        allow_unicode=True,
                        max_length=100,
                        unique=True,
                        verbose_name="slug",
                    ),
                ),
                (
                    "legacy_existing_synonyme",
                    models.ForeignKey(
                        blank=True,
                        help_text="Référence vers le synonyme legacy dont ce tag est issu.",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="search_tag_reference",
                        to="qfdmd.synonyme",
                        verbose_name="Synonyme legacy associé",
                    ),
                ),
            ],
            options={
                "verbose_name": "Synonyme de recherche",
                "verbose_name_plural": "Synonymes de recherche",
            },
            bases=("search.searchterm", models.Model),
        ),
        migrations.CreateModel(
            name="TaggedSearchTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "content_object",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="search_tags_items",
                        to="qfdmd.produitpage",
                    ),
                ),
                (
                    "tag",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tagged_produit_page",
                        to="qfdmd.searchtag",
                    ),
                ),
            ],
            options={
                "verbose_name": "Synonyme de recherche",
                "verbose_name_plural": "Synonymes de recherche",
            },
        ),
        migrations.AddField(
            model_name="produitpage",
            name="search_tags",
            field=modelcluster.contrib.taggit.ClusterTaggableManager(
                blank=True,
                help_text="A comma-separated list of tags.",
                through="qfdmd.TaggedSearchTag",
                to="qfdmd.SearchTag",
                verbose_name="Synonyme de recherche",
            ),
        ),
        # Step 1: Add searchterm_ptr as nullable
        migrations.AddField(
            model_name="synonyme",
            name="searchterm_ptr",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                to="search.searchterm",
            ),
        ),
        migrations.RemoveField(
            model_name="synonyme",
            name="id",
        ),
        migrations.AlterField(
            model_name="synonyme",
            name="searchterm_ptr",
            field=models.OneToOneField(
                auto_created=True,
                on_delete=django.db.models.deletion.CASCADE,
                parent_link=True,
                primary_key=True,
                serialize=False,
                to="search.searchterm",
            ),
        ),
        migrations.AddField(
            model_name="synonyme",
            name="imported_as_search_tag",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "Si renseigné, ce synonyme a été importé comme SearchTag "
                    "et ne devrait plus apparaître dans les résultats de recherche."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="imported_synonymes",
                to="qfdmd.searchtag",
                verbose_name="Importé comme SearchTag",
            ),
        ),
        migrations.AddField(
            model_name="produitpage",
            name="migree_depuis_synonymes_legacy",
            field=models.BooleanField(
                default=False,
                verbose_name="Migration des synonymes effectuée",
            ),
        ),
    ]
