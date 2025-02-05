import json

from django.contrib.admin.utils import quote
from django.template.defaulttags import register
from django.utils.safestring import mark_safe


@register.filter
def options_in_json(optgroups):
    return mark_safe(
        json.dumps(
            [
                option["label"]
                for _, group_choices, _ in optgroups
                for option in group_choices
            ],
            ensure_ascii=False,
        )
    )


@register.filter
def valuetype(value):
    return type(value).__name__


@register.filter(name="quote")
def quote_filter(value):
    return quote(value)
