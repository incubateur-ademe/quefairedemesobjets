import uuid

from django import forms
from django.urls import reverse


class NextAutocompleteInput(forms.TextInput):
    template_name = "ui/forms/widgets/autocomplete/input.html"

    # Class attributes for configuration (can be overridden in subclasses)
    search_view = None
    limit = 5
    navigate = False
    display_value = False
    show_on_focus = False

    def __init__(
        self,
        search_view=None,
        limit=None,
        navigate=None,
        display_value=None,
        show_on_focus=None,
        wrapper_attrs=None,
        *args,
        **kwargs,
    ):
        # Use instance parameters if provided, otherwise fall back to class attributes
        self.search_view = search_view if search_view is not None else self.search_view
        self.limit = limit if limit is not None else self.limit
        self.navigate = navigate if navigate is not None else self.navigate
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
        endpoint_url = reverse(self.search_view)
        return {
            **context,
            "endpoint_url": endpoint_url,
            "limit": self.limit,
            "navigate": self.navigate,
            "display_value": self.display_value,
            "show_on_focus": self.show_on_focus,
            "turbo_frame_id": self.turbo_frame_id,
            "wrapper_attrs": self.wrapper_attrs,
        }


class SynonymeAutocompleteInput(NextAutocompleteInput):
    """Autocomplete widget for Synonyme objects."""

    search_view = "autocomplete_synonyme"
    limit = 5


class HomeSearchAutocompleteInput(NextAutocompleteInput):
    """Autocomplete widget for homepage search."""

    search_view = "qfdmd:autocomplete_home_search"
    limit = 10
    navigate = True
