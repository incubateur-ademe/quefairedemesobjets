from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def a11y_label(context, name):
    """Label from the "Accessibilité" Wagtail setting, also for templates
    rendered without a request."""
    from qfdmd.models import AccessibilitySettings

    settings = AccessibilitySettings.load(request_or_site=context.get("request"))
    return getattr(settings, name)
