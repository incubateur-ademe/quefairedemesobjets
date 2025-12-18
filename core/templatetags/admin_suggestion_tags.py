from django.template.defaulttags import register

from data.models.suggestion import SuggestionGroupe


@register.filter
def is_not_editable(key):
    return key in SuggestionGroupe.NOT_EDITABLE_FIELDS
