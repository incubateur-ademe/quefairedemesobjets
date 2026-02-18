import uuid

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.urls import NoReverseMatch, reverse


class NextAutocompleteInput(forms.TextInput):
    """
    Autocomplete input widget with dynamic search capabilities.

    Usage:
    1. By subclassing (recommended for reusable widgets):
        class MyAutocomplete(NextAutocompleteInput):
            search_view = "my_search_view"
            limit = 10
            show_on_focus = True

    2. By passing parameters (for one-off usage):
        widget = NextAutocompleteInput(
            search_view="my_search_view",
            limit=10,
            show_on_focus=True
        )

    """

    template_name = "ui/forms/widgets/autocomplete/input.html"

    # Class attributes for configuration (can be overridden in subclasses)
    search_view: str | None = None
    limit: int = 5
    display_value: bool = False
    show_on_focus: bool = False

    def __init__(
        self,
        search_view: str | None = None,
        limit: int | None = None,
        display_value: bool | None = None,
        show_on_focus: bool | None = None,
        wrapper_attrs: dict | None = None,
        *args,
        **kwargs,
    ):
        # Use instance parameters if provided, otherwise fall back to class attributes
        self.limit = limit if limit is not None else self.limit
        self.display_value = (
            display_value if display_value is not None else self.display_value
        )
        self.show_on_focus = (
            show_on_focus if show_on_focus is not None else self.show_on_focus
        )
        self.turbo_frame_id = str(uuid.uuid4())
        self.wrapper_attrs = wrapper_attrs or {}

        if self.search_view is None:
            raise ValueError(
                f"{self.__class__.__name__} requires either a 'search_view' class "
                "attribute or a 'search_view' parameter in __init__."
            )

        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)

        # Validate that the view is actually registered in Django's URL configuration
        try:
            endpoint_url = reverse(self.search_view)
        except NoReverseMatch:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__}: The view '{self.search_view}' is not "
                f"registered in Django's URL configuration. Please add it to your "
                f"urlpatterns or check for typos in the view name."
            )

        return {
            **context,
            "endpoint_url": endpoint_url,
            "limit": self.limit,
            "display_value": self.display_value,
            "show_on_focus": self.show_on_focus,
            "turbo_frame_id": self.turbo_frame_id,
            "wrapper_attrs": self.wrapper_attrs,
        }


class HeaderSearchAutocompleteInput(NextAutocompleteInput):
    """Autocomplete widget for homepage search."""

    search_view = "qfdmd:autocomplete_home_search"
    show_on_focus = True
    limit = 10
