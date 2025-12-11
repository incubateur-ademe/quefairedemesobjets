import json
import logging
from math import sqrt

from django.db.models import Q
from django.template.defaulttags import register
from django.template.loader import render_to_string

from core.constants import DEFAULT_MAP_CONTAINER_ID, MAP_CONTAINER_ID
from core.templatetags.acteur_tags import acteur_url
from qfdmo.models import DisplayedActeur
from qfdmo.models.action import get_actions_by_direction
from qfdmo.models.config import CarteConfig, GroupeActionConfig

logger = logging.getLogger(__name__)


@register.simple_tag
def actions_for(dispayed_acteur: DisplayedActeur, direction):
    return dispayed_acteur.acteur_actions(direction=direction)


@register.simple_tag(takes_context=True)
def action_by_direction(context, direction):
    from qfdmo.forms import ActionDirectionForm

    """Get action for the given direction following context"""
    request = context["request"]
    action_direction_form: ActionDirectionForm = context["action_direction_form"]
    requested_direction = action_direction_form["direction"].value()

    action_displayed = request.GET.get("action_displayed", "")
    actions_to_display = get_actions_by_direction()[direction]

    if action_displayed:
        actions_to_display = [
            a for a in actions_to_display if a["code"] in action_displayed.split("|")
        ]

    if action_list := (
        None if requested_direction != direction else request.GET.get("action_list")
    ):
        return [
            {
                **a,
                "active": bool(a["code"] in action_list),
            }
            for a in actions_to_display
        ]
    return [{**a, "active": True} for a in actions_to_display]


@register.simple_tag(takes_context=True)
def hide_object_filter(context):
    """should hide the object filter?"""
    request = context["request"]
    return (
        bool(request.GET.get("sc_id"))
        and request.GET.get("map_container_id") != DEFAULT_MAP_CONTAINER_ID
    )


@register.simple_tag(takes_context=True)
def distance_to_acteur(context, acteur):
    """distance from user location to displayed acteur"""
    request = context["request"]
    longitude = request.GET.get("longitude")
    latitude = request.GET.get("latitude")
    location = acteur.location

    if not (longitude and latitude and location and not acteur.is_digital):
        return ""

    distance_meters = (
        sqrt((location.y - float(latitude)) ** 2 + (location.x - float(longitude)) ** 2)
        * 111320
    )
    if distance_meters >= 1000:
        return f"{round(distance_meters / 1000, 1)} km".replace(".", ",")
    else:
        return f"{round(distance_meters / 10) * 10} m"


@register.filter
def tojson(value):
    """Django filter to replace Jinja2's |tojson filter"""
    return json.dumps(value)


@register.filter
def title_case(value):
    """Django filter to properly handle title case like Jinja2"""
    if value:
        return value.title()
    return value


@register.simple_tag
def random_range(max_value):
    """Generate a random number for cache busting"""
    import random

    return random.randint(0, max_value - 1)


@register.filter
def to_latlng_json(point):
    return json.dumps({"latitude": point.y, "longitude": point.x})


@register.inclusion_tag("templatetags/acteur_pinpoint.html", takes_context=True)
def acteur_pinpoint_tag(
    context,
    acteur,
    direction=None,
    action_list=None,
    carte=None,
    carte_config=None,
    sous_categorie_id=None,
    counter=None,
    force_visible=False,
):
    """
    Template tags to display the acteur's pinpoint after increasing context with
      - marker_icon
      - marker_couleur
      - marker_icon_file
      - marker_bonus
      - marker_fill_background
      - marker_icon_extra_classes
    """
    # Generate mask_id early to ensure it's included in all return paths
    mask_id = acteur.uuid
    if MAP_CONTAINER_ID in context:
        mask_id += f"-{context[MAP_CONTAINER_ID]}"
    if counter:
        mask_id += f"-{counter}"

    tag_context = {
        "latitude": acteur.latitude,
        "longitude": acteur.longitude,
        "href": acteur_url(context, acteur, with_map=False),
        "request": context.get("request"),
        MAP_CONTAINER_ID: context.get(MAP_CONTAINER_ID),
        "mask_id": mask_id,
        "marker_icon": "",
        "marker_couleur": "",
        "marker_icon_file": "",
        "marker_bonus": False,
        "marker_fill_background": False,
        "marker_icon_extra_classes": "",
    }

    action_to_display = acteur.action_to_display(
        direction=direction,
        action_list=action_list,
        sous_categorie_id=sous_categorie_id,
        carte=bool(carte),
    )

    if action_to_display is None:
        logger.warning("No actions found for acteur %s", acteur)
        return tag_context

    # Use precomputed icon_lookup from context if available (optimized path)
    icon_lookup = context.get("icon_lookup", {})
    if icon_lookup and action_to_display:
        acteur_type_code = acteur.acteur_type.code if acteur.acteur_type else None

        # Try to find icon in lookup: first with specific acteur_type, then without
        icon_url = (
            icon_lookup.get((action_to_display.code, acteur_type_code))
            or icon_lookup.get((action_to_display.code, None))
            or icon_lookup.get((None, acteur_type_code))
            or icon_lookup.get((None, None))
        )

        if icon_url:
            tag_context.update(
                marker_icon_file=icon_url,
                marker_icon="",
            )
            return tag_context

    # Fallback to old query-based approach if icon_lookup not available
    elif carte_config:
        queryset = Q()
        if action_to_display:
            queryset &= Q(
                groupe_action__actions__code__in=[action_to_display.code]
            ) | Q(groupe_action__actions__code=None)

        if acteur.acteur_type:
            queryset &= Q(acteur_type=acteur.acteur_type) | Q(acteur_type=None)

        try:
            groupe_action_config = carte_config.groupe_action_configs.get(queryset)
            if groupe_action_config.icon:
                # Property is camelcased as it is used in javascript
                tag_context.update(
                    marker_icon_file=groupe_action_config.icon.url,
                    marker_icon="",
                )
                return tag_context

        except GroupeActionConfig.DoesNotExist:
            pass

    if carte:
        if action_to_display.groupe_action:
            action_to_display = action_to_display.groupe_action
        if action_to_display.code == "reparer":
            tag_context.update(
                marker_bonus=getattr(acteur, "is_bonus_reparation", False),
                marker_fill_background=True,
                marker_icon_extra_classes="qf-text-white",
            )

    tag_context.update(
        marker_icon=action_to_display.icon,
        marker_couleur=action_to_display.couleur,
    )

    return tag_context


@register.inclusion_tag("templatetags/acteur_pinpoint.html")
def location_pinpoint_tag(
    latitude,
    longitude,
    color="blue",
    draggable=False,
):
    return {
        "latitude": latitude,
        "longitude": longitude,
        "marker_icon": "",
        "marker_couleur": color,
        "mask_id": color,
        "marker_icon_file": "",
        "marker_bonus": False,
        "marker_fill_background": draggable,
        "marker_icon_extra_classes": "",
        "draggable": draggable,
    }


def render_acteur_table_row(acteur, context):
    """This is used to render a DSFR-compliant table row."""
    _context = {
        "map_container_id": context["map_container_id"],
        "forms": context["forms"],
        "object": acteur,
        "request": context["request"],
    }
    return [
        render_to_string("ui/components/acteur/acteur_labels.html", _context),
        render_to_string("ui/components/acteur/acteur_services.html", _context),
        distance_to_acteur(context, acteur),
        render_to_string("ui/components/acteur/acteur_lien.html", _context),
    ]


@register.inclusion_tag("ui/components/acteur/acteur_table.html", takes_context=True)
def acteurs_table(context, acteurs):
    """We use a wrapper template tag to use the django-dsfr component.
    As it must be rendered with a dict, we cannot easily render complex rows."""
    return {
        "table": {
            "header": ["Nom du lieu", "Actions", "Distance", ""],
            "content": [render_acteur_table_row(acteur, context) for acteur in acteurs],
            "extra_classes": "fr-table--mode-liste fr-table--multiline qf-w-full",
        }
    }


@register.inclusion_tag("templatetags/carte.html", takes_context=True)
def carte(context: dict, carte_config: CarteConfig) -> dict:
    """
    Render an embedded carte (map) in a turbo-frame for a Wagtail page.
    Used in Wagtail StreamField blocks to display interactive maps of actors
    filtered by the page's sous-categories (subcategories).
    """
    # TODO: add cache
    page = context.get("page")
    return {
        # TODO: Mutualiser avec le _get_map_container_id de views/carte.py
        "id": carte_config.slug,
        "url": carte_config.get_absolute_url(
            override_sous_categories=list(
                page.sous_categorie_objet.all().values_list("id", flat=True)
            ),
            initial_query_string=carte_config.SOLUTION_TEMPORAIRE_A_SUPPRIMER_DES_QUE_POSSIBLE_parametres_url,
        ),
    }


@register.inclusion_tag("templatetags/carte.html", takes_context=True)
def legacy_produit_carte(context: dict, slug: str = "product") -> dict:
    """
    Render an embedded carte (map) in a turbo-frame for a legacy product detail page.
    Used in assistant product pages to display interactive maps of actors
    filtered by the product's sous-categories (subcategories).
    """
    # TODO: add cache
    produit = context.get("produit")
    # Get query string
    sous_categories_ids = produit.sous_categories.all().values_list("id", flat=True)
    carte_config = CarteConfig.objects.get(slug=slug)

    return {
        # TODO: Mutualiser avec le _get_map_container_id de views/carte.py
        "id": carte_config.slug,
        "url": carte_config.get_absolute_url(
            override_sous_categories=list(sous_categories_ids),
        ),
    }
