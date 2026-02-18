from django import template
from django.template.context import Context

register = template.Library()


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
