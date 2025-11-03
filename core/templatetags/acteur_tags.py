from urllib.parse import urlencode

from django.template.defaulttags import register

from core.constants import MAP_CONTAINER_ID
from core.exceptions import TurboFrameConfigurationError


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
        return f"{acteur.full_url}?{querystring}"

    return acteur.full_url


@register.simple_tag(takes_context=True)
def acteur_frame_id(context):
    if MAP_CONTAINER_ID not in context:
        raise TurboFrameConfigurationError(
            f"The view should have a {MAP_CONTAINER_ID} context variable."
        )
    return f"{context.get(MAP_CONTAINER_ID)}:acteur-detail"
