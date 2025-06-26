from django import template

register = template.Library()


@register.filter(is_safe=False)
def iframe(querydict, templates_path):
    if_iframe, if_standalone = templates_path.split(",")

    if "iframe" in querydict:
        return if_iframe
    return if_standalone
