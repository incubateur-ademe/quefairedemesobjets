from typing import Any

from django import forms


class GetFormMixin(forms.Form):
    """A mixin that conditionally initializes form data based on whether matching
    prefixed fields exist in the request data with non-empty values."""

    def __init__(
        self,
        data: dict[str, Any] | None = None,
        prefix: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if prefix:
            self.prefix = prefix

        # TODO: dynamiser liste ici
        unique_field_names_with_prefix = set(
            [self.add_prefix(field) for field in self.base_fields.keys()]
        )
        if data is not None:
            unique_keys = set(data.keys())
            matching_field_names = unique_keys & unique_field_names_with_prefix

            # Only bind form if there are matching fields with non-empty values
            should_bind_form = False
            for field_name in matching_field_names:
                field_value = data.get(field_name)

                # For lists, check if any element is truthy
                if isinstance(field_value, list):
                    if any(field_value):
                        should_bind_form = True
                        break
                # For other types, check if value is truthy
                elif field_value:
                    should_bind_form = True
                    break

            if not should_bind_form:
                data = None

        super().__init__(*args, data=data, **kwargs)
