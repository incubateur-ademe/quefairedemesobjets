import json

from diff_match_patch import diff_match_patch
from django.contrib.admin.utils import quote
from django.template.defaulttags import register
from django.utils.safestring import mark_safe


@register.filter
def diff_display(old_value, new_value):
    """
    Template filter pour afficher les différences entre deux valeurs en utilisant
    diff-match-patch.
    """
    if old_value == new_value:
        return str(new_value)

    dmp = diff_match_patch()
    diffs = dmp.diff_main(str(old_value), str(new_value))
    dmp.diff_cleanupSemantic(diffs)

    result = []
    for op, text in diffs:
        if op == 0:  # égal
            result.append(text)
        elif op == -1:  # supprimé
            result.append(
                f'<span style="color: red; text-decoration: line-through;">{text}'
                "</span>"
            )
        elif op == 1:  # ajouté
            result.append(f'<span style="color: green;">{text}</span>')

    return mark_safe("".join(result))


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
