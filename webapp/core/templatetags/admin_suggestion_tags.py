from django.template.defaulttags import register

from data.models.suggestions.source import SuggestionSourceModel


@register.filter
def suggestion_is_editable(key):
    if isinstance(key, list) or isinstance(key, tuple):
        return all(
            field not in SuggestionSourceModel.get_not_editable_fields()
            for field in key
        )
    return key not in SuggestionSourceModel.get_not_editable_fields()


@register.filter
def suggestion_is_reportable_on_revision(key):
    if isinstance(key, list) or isinstance(key, tuple):
        return all(
            field not in SuggestionSourceModel.get_not_reportable_on_revision_fields()
            for field in key
        )
    return key not in SuggestionSourceModel.get_not_reportable_on_revision_fields()


@register.filter
def suggestion_is_reportable_on_parent(key):
    if isinstance(key, list) or isinstance(key, tuple):
        return all(
            field not in SuggestionSourceModel.get_not_reportable_on_parent_fields()
            for field in key
        )
    return key not in SuggestionSourceModel.get_not_reportable_on_parent_fields()
