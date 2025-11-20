from urllib.parse import urlencode

from django.template.defaulttags import register

from core.templatetags.turbo_tags import namespaced


@register.simple_tag(takes_context=True)
def acteur_url(context: dict, acteur, with_map: bool = True) -> str:
    """
    Generate a URL for an acteur detail page, preserving current query parameters.
    Used in carte templates to create Turbo Frame-compatible links that maintain
    search context and optionally preserve map state when navigating to actor details.
    """
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
def acteur_frame_id(context: dict) -> str:
    """
    Generate the Turbo Frame ID for the acteur detail panel.
    Used to coordinate Turbo Frame navigation between acteur links and the detail panel,
    enabling seamless loading of actor details without full page reloads. The frame ID
    is scoped to the map container to support multiple independent instances.
    """
    return namespaced(context, "acteur-detail")
