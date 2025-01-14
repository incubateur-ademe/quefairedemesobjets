from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def url_keep_qs(context, view_name, *args, **kwargs):
    url = reverse(view_name, args=args, kwargs=kwargs)
    request = context.get("request")
    if request.GET:
        querystring = request.GET.urlencode()
        url = f"{url}?{querystring}"

    return mark_safe(url)
