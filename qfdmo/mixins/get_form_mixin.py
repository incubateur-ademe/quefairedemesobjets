from typing import Any

from django import forms


class GetFormMixin(forms.Form):
    """A mixin that conditionally initializes form data based on whether matching
    prefixed fields exist in the request data."""

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        prefix: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if prefix:
            self.prefix = prefix

        unique_field_names_with_prefix = set(
            [self.add_prefix(field) for field in self.base_fields.keys()]
        )
        if data is not None:
            unique_keys = set(data.keys())
            request_contains_field_names = unique_keys & unique_field_names_with_prefix

            if not request_contains_field_names:
                data = None

        super().__init__(*args, data=data, **kwargs)
