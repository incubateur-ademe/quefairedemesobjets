from html import escape

from django.template.defaulttags import register
from django.utils.safestring import mark_safe


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
