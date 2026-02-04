from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import QuerySet
from modelsearch import index
from modelsearch.queryset import SearchableQuerySetMixin
from wagtail.snippets.models import register_snippet


class SearchTermQuerySet(SearchableQuerySetMixin, QuerySet):
    pass


@register_snippet
class SearchTerm(index.Indexed, models.Model):
    """
    A model that holds search terms for various content types.
    This enables unified search across different models like ProduitPage and FamilyPage.
    """

    objects = SearchTermQuerySet.as_manager()

    # Supported content types for the search feature
    supported_content_types = [
        ("qfdmd", "produitpage"),
        ("qfdmd", "familypage"),
        ("qfdmd", "searchtag"),
        ("qfdmd", "synonyme"),
    ]

    # The search term text, usually displayed in the frontend
    term = models.CharField(max_length=255, db_index=True)

    # Search variants - additional terms that should match this search term
    # This field is indexed for search but not displayed
    search_variants = models.TextField(
        verbose_name="Variantes de recherche",
        blank=True,
        default="",
        help_text=(
            "Variantes de recherche séparées par des virgules ou des retours à la ligne"
        ),
    )

    # Legacy flag - indicates if this search term comes from a legacy model (Synonyme)
    legacy = models.BooleanField(
        verbose_name="Legacy",
        default=False,
        help_text="Indique si ce terme de recherche provient d'un modèle legacy",
    )

    # URL for the search result, used for links in search dropdowns
    url = models.CharField(max_length=500, blank=True, default="")

    # GenericForeignKey for the main object
    # Note: Using "linked_" prefix to avoid conflict with django-modelsearch's
    # internal "object_id" annotation
    linked_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="search_terms",
    )
    linked_object_id = models.PositiveIntegerField()
    object = GenericForeignKey("linked_content_type", "linked_object_id")

    # GenericForeignKey for the parent object (used in frontend display)
    parent_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="search_terms_as_parent",
        null=True,
        blank=True,
    )
    parent_object_id = models.PositiveIntegerField(null=True, blank=True)
    parent_object = GenericForeignKey("parent_content_type", "parent_object_id")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Terme de recherche"
        verbose_name_plural = "Termes de recherche"
        indexes = [
            models.Index(fields=["linked_content_type", "linked_object_id"]),
            models.Index(fields=["parent_content_type", "parent_object_id"]),
        ]
        unique_together = [["linked_content_type", "linked_object_id"]]

    def __str__(self):
        return self.term

    @classmethod
    def get_supported_content_types(cls) -> models.QuerySet[ContentType]:
        from django.db.models import Q

        queries = Q()
        for app_label, model in cls.supported_content_types:
            queries |= Q(app_label=app_label, model=model)

        return ContentType.objects.filter(queries)

    # Static search fields for indexing
    search_fields = [
        index.SearchField("term"),
        index.AutocompleteField("term"),
        index.SearchField("search_variants"),
        index.AutocompleteField("search_variants"),
    ]

    @classmethod
    def sync_from_object(cls, obj):
        """
        Create or update a SearchTerm from an object that implements
        the SearchTermSyncMixin interface.
        """
        content_type = ContentType.objects.get_for_model(obj)

        # Get parent object info if available
        parent_object = None
        parent_content_type = None
        parent_object_id = None

        if hasattr(obj, "get_search_term_parent_object"):
            parent_object = obj.get_search_term_parent_object()
            if parent_object:
                parent_content_type = ContentType.objects.get_for_model(parent_object)
                parent_object_id = parent_object.pk

        # Get the URL if available
        url = ""
        if hasattr(obj, "get_search_term_url"):
            url = obj.get_search_term_url() or ""

        # Get the term (truncate to max_length of 255)
        term = ""
        if hasattr(obj, "get_search_term_verbose_name"):
            term = obj.get_search_term_verbose_name()[:255]

        # Get the legacy flag if available
        legacy = False
        if hasattr(obj, "get_search_term_legacy"):
            legacy = obj.get_search_term_legacy()

        # Get the search variants if available
        search_variants = ""
        if hasattr(obj, "get_search_term_variants"):
            search_variants = obj.get_search_term_variants() or ""

        search_term, created = cls.objects.update_or_create(
            linked_content_type=content_type,
            linked_object_id=obj.pk,
            defaults={
                "term": term,
                "url": url,
                "parent_content_type": parent_content_type,
                "parent_object_id": parent_object_id,
                "legacy": legacy,
                "search_variants": search_variants,
            },
        )

        return search_term, created

    @classmethod
    def delete_for_object(cls, obj):
        """Delete SearchTerm for the given object.
        This is usually called in the delete method of classes
        that needs to sync their removal with their SearchTerm,
        Wagtail pages' SearchTag for example."""
        content_type = ContentType.objects.get_for_model(obj)
        cls.objects.filter(
            linked_content_type=content_type, linked_object_id=obj.pk
        ).delete()
