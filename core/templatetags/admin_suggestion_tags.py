from django.template.defaulttags import register

from data.models.suggestions.source import SuggestionSourceModel


@register.filter
def is_not_editable(key):
    if isinstance(key, list) or isinstance(key, tuple):
        return any(
            field in SuggestionSourceModel.get_not_editable_fields() for field in key
        )
    return key in SuggestionSourceModel.get_not_editable_fields()
