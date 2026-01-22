from abc import abstractmethod


class SearchTermSyncMixin:
    """
    A mixin that automatically syncs a model with the SearchTerm model.

    This mixin is designed to work with both Wagtail Page models
    (which already inherit from index.Indexed) and regular Django models.

    Models inheriting from this mixin must implement:
    - get_search_term_verbose_name(): Returns the term string for search
    - get_search_term_url(): Returns the URL for the search result
    - get_search_term_parent_object(): Returns the parent object for display
    - get_search_fields(): Returns the search fields for Wagtail indexing
    """

    @abstractmethod
    def get_search_term_verbose_name(self) -> str:
        """
        Returns the verbose name/term that will be used for searching.
        This value is stored in the SearchTerm.term field.
        """
        raise NotImplementedError(
            "Subclasses must implement get_search_term_verbose_name()"
        )

    @abstractmethod
    def get_search_term_url(self) -> str:
        """
        Returns the URL that the search result should link to.
        """
        raise NotImplementedError("Subclasses must implement get_search_term_url()")

    @abstractmethod
    def get_search_term_parent_object(self):
        """
        Returns the parent object that will be displayed alongside the search result.
        This is typically used to show the category or family of the search result.
        Can return None if there is no parent object.
        """
        raise NotImplementedError(
            "Subclasses must implement get_search_term_parent_object()"
        )

    @classmethod
    @abstractmethod
    def get_search_fields(cls) -> list:
        """
        Returns the list of search fields for Wagtail search indexing.
        These fields are used by the SearchTerm model for dynamic search.
        """
        raise NotImplementedError("Subclasses must implement get_search_fields()")

    def get_search_term_variants(self) -> str:
        """
        Returns additional search variants for this object.
        Override this method to provide custom search variants.
        By default, returns the search_variants field if it exists.
        """
        if hasattr(self, "search_variants"):
            return self.search_variants
        return ""

    def save(self, *args, **kwargs):
        """
        Override save to sync with SearchTerm after saving.
        """
        super().save(*args, **kwargs)
        self._sync_search_term()

    def _sync_search_term(self):
        """
        Sync this object with its corresponding SearchTerm.
        """
        # Import here to avoid circular imports
        # Only sync if the model's content type is supported
        from django.contrib.contenttypes.models import ContentType

        from search.models import SearchTerm

        content_type = ContentType.objects.get_for_model(self)
        app_model = (content_type.app_label, content_type.model)

        if app_model in SearchTerm.supported_content_types:
            SearchTerm.sync_from_object(self)

    def delete(self, *args, **kwargs):
        """
        Override delete to remove the associated SearchTerm.
        """
        # Import here to avoid circular imports
        from search.models import SearchTerm

        SearchTerm.delete_for_object(self)
        super().delete(*args, **kwargs)
