import logging

from django.db import models
from django.db.models import Q, QuerySet
from modelsearch import index
from modelsearch.queryset import SearchableQuerySetMixin

logger = logging.getLogger(__name__)


class SearchTermQuerySet(SearchableQuerySetMixin, QuerySet):
    def searchable(self):
        """Exclude SearchTerms that should not appear in search results.
        Mirrors the logic in SearchTerm.get_indexed_objects.
        At the moment, some objects in SearchTerm might end up indexed even if
        they are properly excluded in get_indexed_objects.
        This is a bug that have been raised to django-modelsearch, we will
        work on a resolution there first."""
        excluded_ids = self.model.objects.filter(
            Q(synonyme__isnull=False, synonyme__disabled=True)
            | Q(
                synonyme__isnull=False,
                synonyme__imported_as_search_tag__isnull=False,
            )
            | Q(searchtag__isnull=False, searchtag__tagged_produit_page__isnull=True)
            | Q(
                produitpagesearchterm__isnull=False,
                produitpagesearchterm__produit_page__live=False,
            )
        ).values_list("id", flat=True)
        return self.exclude(id__in=excluded_ids)


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

    @property
    def title(self):
        """
        The title of this search term, used for fuzzy ranking (title_text slot).
        Subclasses must implement get_title().
        """
        return self.get_title()

    def get_title(self):
        if type(self) is not SearchTerm:
            logger.warning(
                "%s does not implement get_title(). "
                "Fuzzy search ranking will be degraded for this model. "
                "Please implement get_title() to return the primary display name.",
                type(self).__name__,
            )
        return ""

    search_fields = [
        index.FilterField("id"),
        index.SearchField("title"),
        index.AutocompleteField("title"),
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
            return produit_page_search_term

        return self

    @classmethod
    def get_indexed_objects(cls):
        from qfdmd.models import ProduitPageSearchTerm, SearchTag, Synonyme

        indexed_objects = super().get_indexed_objects()

        if cls is Synonyme:
            indexed_objects = indexed_objects.exclude(
                imported_as_search_tag__isnull=False
            )

        if cls is SearchTag:
            indexed_objects = indexed_objects.exclude(tagged_produit_page__isnull=True)

        if cls is ProduitPageSearchTerm:
            indexed_objects = indexed_objects.exclude(produit_page__live=False)

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
