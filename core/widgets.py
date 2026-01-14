import uuid

from django import forms
from django.urls import reverse


class NextAutocompleteInput(forms.TextInput):
    template_name = "ui/forms/widgets/autocomplete/input.html"

    def __init__(
        self,
        search_view,
        limit=5,
        navigate=False,
        display_value=False,
        show_on_focus=False,
        wrapper_attrs=None,
        *args,
        **kwargs,
    ):
        # TODO: add optional template args
        self.search_view = search_view
        self.limit = limit
        self.navigate = navigate
        self.display_value = display_value
        self.show_on_focus = show_on_focus
        self.turbo_frame_id = str(uuid.uuid4())
        self.wrapper_attrs = wrapper_attrs or {}

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

    def __init__(self, *args, **kwargs):
        super().__init__(
            search_view="autocomplete_synonyme",
            limit=kwargs.pop("limit", 5),
            *args,
            **kwargs,
        )


class HomeSearchAutocompleteInput(NextAutocompleteInput):
    def __init__(self, *args, **kwargs):
        super().__init__(
            search_view="qfdmd:autocomplete_home_search",
            limit=kwargs.pop("limit", 10),
            navigate=True,
            *args,
            **kwargs,
        )
