from math import sqrt

from django import template

from core.utils import get_direction
from qfdmo.models import DisplayedActeur
from qfdmo.models.action import get_actions_by_direction

register = template.Library()


@register.simple_tag(takes_context=True)
def action_by_direction(context, direction):
    """Template tag to replace jinja2_handler.action_by_direction"""
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


@register.simple_tag
def display_exclusivite_reparation(acteur):
    """Template tag to replace jinja2_handler.display_exclusivite_reparation"""
    if isinstance(acteur, DisplayedActeur):
        return acteur.exclusivite_de_reprisereparation
    return False


@register.simple_tag(takes_context=True)
def hide_object_filter(context):
    """Template tag to replace jinja2_handler.hide_object_filter"""
    request = context["request"]
    return bool(request.GET.get("sc_id"))


@register.simple_tag(takes_context=True)
def distance_to_acteur(context, acteur):
    """Template tag to replace jinja2_handler.distance_to_acteur"""
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
        return f"({round(distance_meters / 1000, 1)} km)".replace(".", ",")
    else:
        return f"({round(distance_meters / 10) * 10} m)"


@register.filter
def tojson(value):
    """Django filter to replace Jinja2's |tojson filter"""
    import json

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
