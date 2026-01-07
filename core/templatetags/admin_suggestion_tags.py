from django.template.defaulttags import register

from data.models.suggestions.source import SuggestionSourceModel


@register.filter
def is_not_editable(key):
    return key in SuggestionSourceModel.get_not_editable_fields()
