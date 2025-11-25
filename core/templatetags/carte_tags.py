import json
import logging
from math import sqrt

from django.template.defaulttags import register
from django.template.loader import render_to_string

from core.constants import DEFAULT_MAP_CONTAINER_ID, MAP_CONTAINER_ID
from qfdmo.models import DisplayedActeur
from qfdmo.models.action import get_actions_by_direction
from qfdmo.models.config import CarteConfig

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
def acteur_pinpoint_tag(context, counter=0):
    """
    Template tags to display the acteur's pinpoint after increasing context with
      - marker_icon
      - marker_couleur
      - marker_icon_file
      - marker_bonus
      - marker_fill_background
      - marker_icon_extra_classes
    """
    acteur = context.get("acteur")
    carte = context.get("carte", None)
    carte_config_icon_urls = context.get("carte_config_icon_urls") or {}
    all_groupe_actions = context.get("all_groupe_actions", {})

    context = {
        "acteur": acteur,
        "request": context.get("request"),
        MAP_CONTAINER_ID: context.get(MAP_CONTAINER_ID),
        "marker_icon": "",
        "marker_couleur": "",
        "marker_icon_file": "",
        "marker_bonus": False,
        "marker_fill_background": False,
        "marker_icon_extra_classes": "",
    }

    groupe_action_to_display = acteur.get_computed_groupe_action(all_groupe_actions)

    if groupe_action_to_display is None:
        logger.warning("No actions found for acteur %s", acteur)
        return context

    carte_config_icon_id = getattr(acteur, "computed_carte_config_icon_id", None)
    if carte_config_icon_id:
        carte_config_icon_url = carte_config_icon_urls.get(carte_config_icon_id)
        if carte_config_icon_url:
            context.update(
                marker_icon_file=carte_config_icon_url,
                marker_icon="",
            )
            return context

    if carte and "reparer" in groupe_action_to_display.code:
        context.update(
            marker_bonus=getattr(acteur, "is_bonus_reparation", False),
            marker_fill_background=True,
            marker_icon_extra_classes="qf-text-white",
        )

    # Generate uuid for svg mask to prevent marker's border to vanish
    mask_id = acteur.uuid
    if MAP_CONTAINER_ID in context:
        mask_id += f"-{context[MAP_CONTAINER_ID]}"

    if counter:
        mask_id += f"-{counter}"

    context.update(
        mask_id=mask_id,
        marker_icon=groupe_action_to_display.icon,
        marker_couleur=groupe_action_to_display.couleur,
    )

    return context


def render_acteur_table_row(acteur, context):
    """This is used to render a DSFR-compliant table row."""
    _context = {
        "map_container_id": context["map_container_id"],
        "forms": context["forms"],
        "object": acteur,
        "request": context["request"],
    }
    return [
        render_to_string("ui/components/carte/acteur/acteur_labels.html", _context),
        render_to_string("ui/components/carte/acteur/acteur_services.html", _context),
        distance_to_acteur(context, acteur),
        render_to_string("ui/components/carte/acteur/acteur_lien.html", _context),
    ]


@register.inclusion_tag(
    "ui/components/carte/acteur/acteur_table.html", takes_context=True
)
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
