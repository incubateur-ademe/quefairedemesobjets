from math import sqrt

from django.http import HttpRequest

from core.utils import get_direction
from qfdmo.models.action import get_actions_by_direction


def action_by_direction(request: HttpRequest, direction: str):
    # TODO: refactor to not use a dict anymore
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


def distance_to_acteur(request, acteur):
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
