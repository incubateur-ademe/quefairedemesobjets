# Migration for SearchTag, Synonyme inheritance, search_variants and search_term

import django.db.models.deletion
import modelcluster.contrib.taggit
import modelcluster.fields
from django.db import migrations, models


def create_search_terms_for_synonymes(apps, schema_editor):
    """Create SearchTerm records for existing Synonyme instances."""
    Synonyme = apps.get_model("qfdmd", "Synonyme")
    SearchTerm = apps.get_model("search", "SearchTerm")

    for synonyme in Synonyme.objects.all():
        search_term = SearchTerm.objects.create()
        synonyme.searchterm_ptr_id = search_term.id
        synonyme.save(update_fields=["searchterm_ptr_id"])


def reverse_search_terms_for_synonymes(apps, schema_editor):
    """Reverse: delete SearchTerm records created for Synonyme instances."""
    Synonyme = apps.get_model("qfdmd", "Synonyme")
    SearchTerm = apps.get_model("search", "SearchTerm")

    search_term_ids = Synonyme.objects.exclude(
        searchterm_ptr_id__isnull=True
    ).values_list("searchterm_ptr_id", flat=True)
    SearchTerm.objects.filter(pk__in=list(search_term_ids)).delete()


def create_search_terms_for_produit_pages(apps, schema_editor):
    """Create a SearchTerm for each existing ProduitPage."""
    ProduitPage = apps.get_model("qfdmd", "ProduitPage")
    SearchTerm = apps.get_model("search", "SearchTerm")

    for page in ProduitPage.objects.all():
        search_term = SearchTerm.objects.create()
        page.search_term = search_term
        page.save(update_fields=["search_term"])


def delete_search_terms_for_produit_pages(apps, schema_editor):
    """Delete SearchTerms associated with ProduitPages."""
    ProduitPage = apps.get_model("qfdmd", "ProduitPage")
    SearchTerm = apps.get_model("search", "SearchTerm")

    search_term_ids = ProduitPage.objects.filter(search_term__isnull=False).values_list(
        "search_term_id", flat=True
    )
    SearchTerm.objects.filter(id__in=list(search_term_ids)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("qfdmd", "0070_produitpage_est_famille"),
        ("search", "0001_initial"),
    ]

    operations = [
        # Create SearchTag model (inherits from SearchTerm)
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
            ],
            options={
                "verbose_name": "Synonyme de recherche",
                "verbose_name_plural": "Synonymes de recherche",
            },
            bases=("search.searchterm", models.Model),
        ),
        # Create TaggedSearchTag through model
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
        # Add search_tags field to ProduitPage
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
        # Step 1: Add searchterm_ptr as nullable field to Synonyme
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
        # Step 2: Populate the field with actual SearchTerm records
        migrations.RunPython(
            create_search_terms_for_synonymes,
            reverse_search_terms_for_synonymes,
        ),
        # Step 3: Remove the old 'id' primary key
        migrations.RemoveField(
            model_name="synonyme",
            name="id",
        ),
        # Step 4: Make searchterm_ptr non-nullable and set as primary key
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
        # Add imported_as_search_tag field to Synonyme
        migrations.AddField(
            model_name="synonyme",
            name="imported_as_search_tag",
            field=models.ForeignKey(
                blank=True,
                help_text="Si renseigné, ce synonyme a été importé comme SearchTag et ne devrait plus apparaître dans les résultats de recherche.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="imported_synonymes",
                to="qfdmd.searchtag",
                verbose_name="Importé comme SearchTag",
            ),
        ),
        # Add search_variants field to ProduitPage (from 0072)
        migrations.AddField(
            model_name="produitpage",
            name="search_variants",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Termes alternatifs permettant de trouver cette page dans la recherche. Ces variantes sont invisibles pour les utilisateurs mais améliorent la recherche. Séparez les termes par des virgules ou des retours à la ligne.",
                verbose_name="Variantes de recherche",
            ),
        ),
        # Add search_term field to ProduitPage (from 0073)
        migrations.AddField(
            model_name="produitpage",
            name="search_term",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="produit_page",
                to="search.searchterm",
            ),
        ),
        # Populate SearchTerm for existing ProduitPages
        migrations.RunPython(
            create_search_terms_for_produit_pages,
            delete_search_terms_for_produit_pages,
        ),
    ]
