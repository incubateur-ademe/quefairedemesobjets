from django.template.defaulttags import register


@register.inclusion_tag("head/favicon.html")
def favicon() -> dict:
    return {}
