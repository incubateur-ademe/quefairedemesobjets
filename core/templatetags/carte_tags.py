import json
import logging
from math import sqrt

from django.db.models import Q
from django.template.defaulttags import register
from django.template.loader import render_to_string

from core.utils import get_direction
from qfdmo.models import DisplayedActeur
from qfdmo.models.action import get_actions_by_direction
from qfdmo.models.config import GroupeActionConfig

logger = logging.getLogger(__name__)


@register.simple_tag
def actions_for(dispayed_acteur: DisplayedActeur, direction):
    return dispayed_acteur.acteur_actions(direction=direction)


@register.simple_tag(takes_context=True)
def action_by_direction(context, direction):
    """Get action for the given direction following context"""
    request = context["request"]
    requested_direction = get_direction(request)
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
        and request.GET.get("map_container_id") != "carte"
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
    context.update(
        {
            "marker_icon": "",
            "marker_couleur": "",
            "marker_icon_file": "",
            "marker_bonus": False,
            "marker_fill_background": False,
            "marker_icon_extra_classes": "",
        }
    )

    action_to_display = acteur.action_to_display(
        direction=direction,
        action_list=action_list,
        sous_categorie_id=sous_categorie_id,
    )

    if action_to_display is None:
        logger.warning("No actions found for acteur %s", acteur)
        return context

    if carte_config:
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
                context.update(
                    {
                        "marker_icon_file": groupe_action_config.icon.url,
                        "marker_icon": "",
                    }
                )
                return context

        except GroupeActionConfig.DoesNotExist:
            pass

    if carte:
        if action_to_display.groupe_action:
            action_to_display = action_to_display.groupe_action
        if action_to_display.code == "reparer":
            context.update(
                {
                    "marker_bonus": getattr(acteur, "is_bonus_reparation", False),
                    "marker_fill_background": True,
                    "marker_icon_extra_classes": "qf-text-white",
                }
            )

    context.update(
        {
            "marker_icon": action_to_display.icon,
            "marker_couleur": action_to_display.couleur,
        }
    )

    return context


@register.simple_tag
def get_non_enseigne_labels_count(acteur):
    """Template tag to get count of labels with type_enseigne=False"""
    return acteur.labels_display.filter(type_enseigne=False).count()


def render_acteur(acteur, context):
    return [
        render_to_string(
            "ui/components/carte/acteur/acteur_labels.html", {"object": acteur}
        ),
        render_to_string(
            "ui/components/carte/acteur/acteur_services.html", {"object": acteur}
        ),
        distance_to_acteur(context, acteur),
        render_to_string(
            "ui/components/carte/acteur/acteur_lien.html",
            {"object": acteur, "map_container_id": context["map_container_id"]},
        ),
    ]


@register.inclusion_tag(
    "ui/components/carte/acteur/acteur_table.html", takes_context=True
)
def acteurs_table(context, acteurs):
    return {
        "table": {
            "header": ["Nom du lieu", "Actions", "Distance", ""],
            "content": [render_acteur(acteur, context) for acteur in acteurs],
            "extra_classes": "fr-table--mode-liste fr-table--multiline qf-w-full",
        }
    }
