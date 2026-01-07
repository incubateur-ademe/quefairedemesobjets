from django.template.defaulttags import register

from data.models.suggestion import SuggestionSourceType


@register.filter
def is_not_editable(key):
    return key in SuggestionSourceType.get_not_editable_fields()
