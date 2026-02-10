from django.db import models
from django.db.models import QuerySet
from modelsearch import index
from modelsearch.queryset import SearchableQuerySetMixin


class SearchTermQuerySet(SearchableQuerySetMixin, QuerySet):
    def exclude_imported_synonymes(self):
        """
        Exclude from search results:
        - Synonymes that have a SearchTag linked to a ProduitPage
          (the SearchTag replaces the synonyme in results)
        - Orphaned SearchTags not linked to any ProduitPage

        Uses evaluated ID lists to avoid complex subqueries that the
        search backend cannot introspect.
        """
        from qfdmd.models import SearchTag, Synonyme, TaggedSearchTag

        # Synonymes replaced by a SearchTag linked to a page
        imported_synonyme_ids = list(
            Synonyme.objects.filter(
                search_tag_reference__in=TaggedSearchTag.objects.values_list(
                    "tag_id", flat=True
                ),
            ).values_list("searchterm_ptr_id", flat=True)
        )

        # Orphaned SearchTags (not linked to any page)
        orphaned_tag_ids = list(
            SearchTag.objects.exclude(
                searchterm_ptr_id__in=TaggedSearchTag.objects.values_list(
                    "tag_id", flat=True
                ),
            ).values_list("searchterm_ptr_id", flat=True)
        )

        return self.exclude(
            id__in=imported_synonyme_ids + orphaned_tag_ids,
        )


class SearchTerm(index.Indexed, models.Model):
    """
    Base model for search terms. Child models (Synonyme, SearchTag) inherit
    from this to enable unified search across different content types.
    """

    search_variants = models.TextField(
        verbose_name="Variantes de recherche",
        blank=True,
        default="",
        help_text=(
            "Termes alternatifs permettant de trouver cette page dans la recherche. "
            "Ces variantes sont invisibles pour les utilisateurs mais améliorent "
            "la recherche. Séparez les termes par des virgules ou des retours "
            "à la ligne."
        ),
    )

    search_fields = [
        index.FilterField("id"),
        index.SearchField("search_variants"),
        index.AutocompleteField("search_variants"),
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
        raise NotImplementedError(
            f"{type(self).__name__} (pk={self.pk}) must define search_result_template"
        )

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

        # Exclude Synonymes that have a SearchTag linked to a ProduitPage
        if cls is Synonyme:
            indexed_objects = indexed_objects.exclude(
                search_tag_reference__tagged_produit_page__isnull=False
            )

        # Exclude orphaned SearchTags (no page and no legacy synonyme)
        if cls is SearchTag:
            indexed_objects = indexed_objects.filter(tagged_produit_page__isnull=False)

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
