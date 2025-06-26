from django import template

register = template.Library()


@register.filter
def iframe(querydict, template_path):
    alternative_path = template_path.replace("html", "iframe.html")

    if "iframe" in querydict:
        return alternative_path

    return template_path
