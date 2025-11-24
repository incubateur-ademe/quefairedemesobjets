from urllib.parse import urlencode

from django.template.defaulttags import register
from django.template.loader import render_to_string

from core.constants import ACTEUR
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


@register.inclusion_tag(
    "ui/components/label_qualite/label_qualite.html", takes_context=True
)
def acteur_label(context, acteur=None):
    if not acteur:
        acteur = context["object"]

    labels_qualite_ordered = acteur.labels_display
    first_label_qualite = labels_qualite_ordered.first()

    label = render_to_string(
        "ui/components/label_qualite/dsfr_label.html", {"label": first_label_qualite}
    )

    if first_label_qualite.code == "bonusrepar":
        return {"label": label}
    else:
        non_enseigne_count = acteur.labels_without_enseigne_display
        if non_enseigne_count > 1:
            return {
                "label": ACTEUR["plusieurs_labels"],
                "extra_classes": "fr-tag--icon-left fr-icon-shield-check-line",
            }
        else:
            return {"label": label}
