from typing import Any


class AutoSubmitMixin:
    """A mixin that automatically adds auto-submit data attributes
    to specified form fields."""

    autosubmit_fields: list[str] = []
    """List of field names that should trigger auto-submit."""

    autosubmit_action: str = "search-solution-form#submitForm"
    """The Stimulus action to add to auto-submit fields."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        action = getattr(self, "autosubmit_action", "search-solution-form#submitForm")

        for field_name in getattr(self, "autosubmit_fields", []):
            field = self.fields.get(field_name)
            if field:
                field.widget.attrs["data-action"] = action
