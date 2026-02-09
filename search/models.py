from django.db import models
from django.db.models import QuerySet
from modelsearch import index
from modelsearch.queryset import SearchableQuerySetMixin
from wagtail.snippets.models import register_snippet


class SearchTermQuerySet(SearchableQuerySetMixin, QuerySet):
    def exclude_imported_synonymes(self):
        """
        Exclude Synonyme instances that have been imported as SearchTags.
        These synonymes have imported_as_search_tag set and should not
        appear in search results (the SearchTag should appear instead).
        """
        return self.exclude(
            synonyme__imported_as_search_tag__isnull=False,
        )


@register_snippet
class SearchTerm(index.Indexed, models.Model):
    """
    Base model for search terms. Child models (Synonyme, SearchTag) inherit
    from this to enable unified search across different content types.
    """

    # search_fields must be non-empty for SearchTerm to be recognized as indexed.
    # This enables searching across all child models (Synonyme, SearchTag) via
    # SearchTerm.objects.search(). Child models define their own search_fields
    # which are used for actual indexing.
    search_fields = [
        index.FilterField("id"),
    ]

    objects = SearchTermQuerySet.as_manager()

    class Meta:
        verbose_name = "Terme de recherche"
        verbose_name_plural = "Termes de recherche"

    def __str__(self):
        # Try to return a meaningful string from child models
        instance = self.get_indexed_instance()
        if instance != self:
            return str(instance)
        return f"SearchTerm {self.pk}"

    @property
    def search_result_template(self):
        return "ui/components/search/_search_result.html"

    def get_indexed_instance(self):
        from qfdmd.models import SearchTag, Synonyme

        """
        Returns the most specific child instance for proper indexing.
        This ensures django-modelsearch indexes all fields from child models.
        """
        synonyme = Synonyme.objects.filter(searchterm_ptr_id=self.id).first()
        if synonyme:
            return synonyme

        search_tag = SearchTag.objects.filter(searchterm_ptr_id=self.id).first()
        if search_tag:
            return search_tag

        # Check if linked to a ProduitPage via OneToOne reverse
        produit_page = getattr(self, "produit_page", None)
        if produit_page:
            return produit_page

        return self

    @classmethod
    def get_indexed_objects(cls):
        from qfdmd.models import SearchTag, Synonyme

        indexed_objects = super().get_indexed_objects()

        # Don't index SearchTerm base class when they have a more specific type
        if cls is SearchTerm:
            indexed_objects = indexed_objects.exclude(
                id__in=Synonyme.objects.values_list("searchterm_ptr_id", flat=True)
            )
            indexed_objects = indexed_objects.exclude(
                id__in=SearchTag.objects.values_list("searchterm_ptr_id", flat=True)
            )

        # Exclude Synonymes that have been imported as SearchTags
        if cls is Synonyme:
            indexed_objects = indexed_objects.exclude(
                imported_as_search_tag__isnull=False
            )

        return indexed_objects

    def get_specific(self):
        """
        Alias for get_indexed_instance for Wagtail-like API consistency.
        Returns the most specific child instance.
        """
        return self.get_indexed_instance()

    @property
    def specific(self):
        """Property alias for get_specific()."""
        return self.get_specific()
