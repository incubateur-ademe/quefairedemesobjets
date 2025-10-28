from urllib.parse import urlencode

from django.template.defaulttags import register


@register.simple_tag(takes_context=True)
def acteur_url(context, acteur, with_map=True):
    query_params = {}
    request = context.get("request")

    if request:
        query_params.update(request.GET.dict())

    if with_map:
        query_params.update(with_map=True)

    if query_params:
        querystring = urlencode(query_params)
        return f"{acteur.url}?{querystring}"

    return acteur.url


@register.simple_tag(takes_context=True)
def acteur_frame_id(context):
    return f"{context.get('map_container_id')}:acteur-detail"
