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

    # TODO: what about other parameters from CarteConfig used in the Acteur URL ?
    # Should we add a logic to set the forms with carte_config parameters ?
    # - redirect to a carte with bounding form ?
    # - get the CarteConfig in adresse_detail view and apply the parameters when display
    #   it : something like /carte/<carte_config.slug>/details/<uuid>, it can be useful
    #   for futur specific setting to be applied in the acteur detail card or for the
    #   share feature ?
    map_container_id = context.get("map_container_id")

    if request:
        query_params.update(request.GET.dict())

    if map_container_id and "map_container_id" not in query_params:
        query_params.update(map_container_id=map_container_id)

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
    """
    Display a single quality label for an acteur in the frontend.

    The frontend displays only one label per acteur, so we need to prioritize which
    label to show. This template tag uses a pre-ordered list of labels where:
    - Bonus labels (bonus=True) appear first
    - Then sorted by type_enseigne
    - Only displayable labels (afficher=True) are included

    The ordering and filtering is done at the database level via Prefetch in the view,
    making this template tag a simple accessor with zero additional queries.
    """
    if not acteur:
        acteur = context["object"]

    # Use prefetched and pre-ordered labels from the view
    # The queryset is already filtered (afficher=True)
    # and ordered (-bonus, type_enseigne)
    displayable_labels = getattr(acteur, "displayable_labels_ordered", [])

    if not displayable_labels:
        return {}

    first_label = displayable_labels[0]

    # If bonus, always show it
    if first_label.bonus:
        first_label.libelle = "Propose le Bonus Réparation"
        dsfr_label = render_to_string(
            "ui/components/label_qualite/dsfr_label.html",
            {"label": first_label},
        )
        return {"label": dsfr_label}

    # For non-bonus labels, check if multiple non-enseigne labels exist
    non_enseigne_labels = [
        label for label in displayable_labels if not label.type_enseigne
    ]

    if len(non_enseigne_labels) > 1:
        return {
            "label": ACTEUR["plusieurs_labels"],
            "extra_classes": "fr-tag--icon-left fr-icon-shield-check-line",
        }
    else:
        dsfr_label = render_to_string(
            "ui/components/label_qualite/dsfr_label.html",
            {"label": first_label},
        )
        return {"label": dsfr_label}


@register.inclusion_tag("ui/components/service/service_tag.html", takes_context=True)
def service_tag(context, text, action):
    """
    Renders a service tag with proper styling based on the action group.
    In formulaire mode, displays action directly with reduced opacity.
    In carte/list mode (default), displays action.groupe_action.
    """
    is_formulaire = context.get("is_formulaire", False)

    # In formulaire mode, use action directly; otherwise use groupe_action
    display_action = action if is_formulaire else action.groupe_action

    return {
        "text": text,
        "action": display_action,
        "extra_classes": "qf-bg-opacity-30" if is_formulaire else "",
    }
