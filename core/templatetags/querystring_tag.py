from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def assistant_iframe_script(context: dict) -> str:
    request = context.get("request")
    if request and "iframe" in request.GET:
        return "?iframe=1"
    return ""
