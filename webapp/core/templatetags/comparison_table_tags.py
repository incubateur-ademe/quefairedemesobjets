import logging
from html import escape

from django.template.defaulttags import register
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


@register.filter
def stimulus_attrs(config):
    """Render a StimulusControllerConfig as HTML data attributes."""
    if config is None:
        return ""
    parts = [f'data-controller="{escape(config.controller)}"']
    for key, value in config.values.items():
        parts.append(
            f'data-{escape(config.controller)}-{escape(key)}-value="{escape(str(value))}"'
        )
    if config.actions:
        parts.append(f'data-action="{escape(" ".join(config.actions))}"')
    return mark_safe(" ".join(parts))


@register.simple_tag(takes_context=True)
def display_cell_as_html(context, cell):
    if cell.cell_type == "html":
        template_name = "data/_partials/cells/html.html"
    elif cell.cell_type == "display":
        template_name = "data/_partials/cells/display.html"
    elif cell.cell_type == "editable":
        template_name = "data/_partials/cells/editable.html"
    elif cell.cell_type == "action":
        template_name = "data/_partials/cells/action.html"
    else:
        raise ValueError(f"Unknown cell type: {cell.cell_type}")
    return mark_safe(
        render_to_string(template_name, {"cell": cell}, request=context.get("request"))
    )
