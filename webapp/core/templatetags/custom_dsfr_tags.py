import re

from django import template
from django.template.context import Context
from django.utils.safestring import mark_safe

register = template.Library()

HEADING_PATTERN = re.compile(r"<(?P<slash>/?)h(?P<level>[1-6])\b")


@register.simple_tag(takes_context=True)
def url_remplace_params(context: Context, **kwargs):
    """
    COPY PASTED FROM https://github.com/numerique-gouv/django-dsfr/blob/064db1a8e98df0c07bfebf071b7a5b38e5706ac0/dsfr/templatetags/dsfr_tags.py
    We need a full absolute url instead of just a querystring
    """
    request = context["request"]
    query = request.GET.copy()

    for k in kwargs:
        query[k] = kwargs[k]

    # Build full absolute URL
    path = request.path
    query_string = query.urlencode()

    if query_string:
        return request.build_absolute_uri(f"{path}?{query_string}")
    return request.build_absolute_uri(path)


@register.simple_tag
def accordions_heading_tag(blocks) -> str:
    """Accordion titles sit one level under the group title, or under the page h1."""
    has_group_title = any(block.block_type == "title" for block in blocks)
    return "h3" if has_group_title else "h2"


@register.filter
def shift_headings(html: str, tag: str) -> str:
    """Re-level rich text headings (authored from h2) under the given tag."""
    offset = int(tag[1]) - 1

    def shift(match: re.Match) -> str:
        level = min(int(match.group("level")) + offset, 6)
        return f"<{match.group('slash')}h{level}"

    return mark_safe(HEADING_PATTERN.sub(shift, str(html)))  # noqa: S308


@register.simple_tag
def only_tiles(blocks) -> bool:
    """True when a stream holds tiles only: they are a list, not headings."""
    return len(blocks) > 0 and all(block.block_type == "tile" for block in blocks)
