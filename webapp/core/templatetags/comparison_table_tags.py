import logging

from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


@register.simple_tag(takes_context=True)
def display_cell_as_html(context, cell):
    return mark_safe(
        render_to_string(
            cell.template_name, {"cell": cell}, request=context.get("request")
        )
    )
