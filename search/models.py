from django.db import models
from django.db.models import QuerySet
from modelsearch import index
from modelsearch.queryset import SearchableQuerySetMixin


class SearchTermQuerySet(SearchableQuerySetMixin, QuerySet):
    pass


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

    search_result_template = "ui/components/search/search_result.html"

    def __init__(self, *args, **kwargs) -> None:
        if not (hasattr(type(self), "search_result_template")):
            raise NotImplementedError(
                f"{type(self).__name__} must define search_result_template"
            )
        return super().__init__(*args, **kwargs)

    def get_indexed_instance(self):
        from qfdmd.models import ProduitPageSearchTerm, SearchTag, Synonyme

        """
        Returns the most specific child instance for proper indexing.
        This ensures django-modelsearch indexes all fields from child models.
        """
        if synonyme := Synonyme.objects.filter(searchterm_ptr_id=self.id).first():
            return synonyme

        if search_tag := SearchTag.objects.filter(searchterm_ptr_id=self.id).first():
            return search_tag

        # Check if linked to a ProduitPage via OneToOne reverse
        if produit_page_search_term := ProduitPageSearchTerm.objects.filter(
            searchterm_ptr_id=self.id
        ).first():
            return produit_page_search_term.produit_page

        return self

    @classmethod
    def get_indexed_objects(cls):
        from qfdmd.models import SearchTag, Synonyme

        indexed_objects = super().get_indexed_objects()

        if cls is Synonyme:
            indexed_objects = indexed_objects.exclude(
                imported_as_search_tag__isnull=False
            )

        if cls is SearchTerm:
            # Don't index standalone search terms
            indexed_objects = indexed_objects.none()

        if cls is SearchTag:
            indexed_objects = indexed_objects.exclude(tagged_produit_page__isnull=True)

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
