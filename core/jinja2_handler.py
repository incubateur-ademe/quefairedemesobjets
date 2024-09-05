from math import sqrt
from urllib.parse import quote_plus

from django.conf import settings
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse

from core.utils import get_direction
from jinja2 import Environment
from qfdmo.models import CachedDirectionAction, DisplayedActeur


def is_embedded(request: HttpRequest) -> bool:
    return "iframe" in request.GET or "carte" in request.GET


def is_carte(request: HttpRequest) -> bool:
    return "carte" in request.GET


def is_iframe(request: HttpRequest) -> bool:
    return "iframe" in request.GET


def action_by_direction(request: HttpRequest, direction: str):
    requested_direction = get_direction(request)
    action_displayed = request.GET.get("action_displayed", "")
    actions_to_display = CachedDirectionAction.get_actions_by_direction()[direction]
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


def display_infos_panel(adresse: DisplayedActeur) -> bool:
    return (
        bool(adresse.horaires_description or adresse.display_postal_address())
        and not adresse.is_digital
    )


def display_exclusivite_reparation(acteur: DisplayedActeur) -> bool:
    return acteur.exclusivite_de_reprisereparation


def hide_object_filter(request) -> bool:
    return bool(request.GET.get("sc_id"))


def distance_to_acteur(request, adresse):
    long = request.GET.get("longitude")
    lat = request.GET.get("latitude")
    point = adresse.location

    if long and lat and point and not adresse.is_digital:
        dist = sqrt((point.y - float(lat)) ** 2 + (point.x - float(long)) ** 2) * 111320
        return (
            f"({str(round(dist/1000,1)).replace('.',',')} km)"
            if dist >= 1000
            else f"({round(dist/10)*10} m)"
        )
    return ""


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "action_by_direction": action_by_direction,
            "display_infos_panel": display_infos_panel,
            "hide_object_filter": hide_object_filter,
            "distance_to_acteur": distance_to_acteur,
            "display_exclusivite_reparation": display_exclusivite_reparation,
            "is_embedded": is_embedded,
            "is_iframe": is_iframe,
            "is_carte": is_carte,
            "url": reverse,
            "static": static,
            "quote_plus": lambda u: quote_plus(u),
            "ENVIRONMENT": settings.ENVIRONMENT,
            "AIRFLOW_WEBSERVER_REFRESHACTEUR_URL": (
                settings.AIRFLOW_WEBSERVER_REFRESHACTEUR_URL
            ),
        }
    )
    return env
