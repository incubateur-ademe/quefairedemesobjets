import difflib
from math import sqrt
from typing import List
from urllib.parse import quote_plus

from django.conf import settings
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse

from core.utils import get_direction
from jinja2 import Environment
from qfdmo.models import CachedDirectionAction, DisplayedActeur


# FIXME : could be tested
def str_diff(s1: str | None, s2: str | None) -> str:
    s1 = s1 or ""
    s2 = s2 or ""
    d = difflib.Differ().compare(s1, s2)
    list_diff = []
    for letter in list(d):
        if letter[0] == "+":
            list_diff.append(f'<span class="qfdmo-bg-red-500" >{letter[-1]}</span>')
        elif letter[0] == "-":
            list_diff.append(
                f'<span class="qfdmo-bg-green-500"'
                f' style="background-color:greenyellow;">{letter[-1]}</span>'
            )
        else:
            list_diff.append(letter[-1])
    return "".join(list_diff)


def is_embedded(request: HttpRequest) -> bool:
    return "iframe" in request.GET or "carte" in request.GET


def is_carte(request: HttpRequest) -> bool:
    return "carte" in request.GET


def is_iframe(request: HttpRequest) -> bool:
    return "iframe" in request.GET


# FIXME : perhaps it is better in util list ?
def get_action_list(request: HttpRequest) -> List[dict]:
    direction = get_direction(request)
    if action_list := request.GET.get("action_list"):
        return [
            a
            for a in CachedDirectionAction.get_actions_by_direction()[direction]
            if a["code"] in action_list.split("|")
        ]
    else:
        return CachedDirectionAction.get_actions_by_direction()[direction]


def action_list_display(request: HttpRequest) -> List[str]:
    return [action["libelle"] for action in get_action_list(request)]


def action_by_direction(request: HttpRequest, direction: str):
    action_list = request.GET.get("action_list")
    requested_direction = get_direction(request)
    if requested_direction != direction:
        action_list = None
    if action_list:
        return [
            {
                **a,
                "active": bool(a["code"] in action_list),
            }
            for a in CachedDirectionAction.get_actions_by_direction()[direction]
        ]
    return [
        {
            **a,
            "active": True,
        }
        for a in CachedDirectionAction.get_actions_by_direction()[direction]
    ]


def display_search(request: HttpRequest) -> bool:
    return not is_carte(request)


def display_infos_panel(adresse: DisplayedActeur) -> bool:
    return (
        bool(adresse.horaires_description or adresse.adresse) and not adresse.is_digital
    )


def display_labels_panel(adresse: DisplayedActeur) -> bool:
    return bool(adresse.labels.filter(afficher=True, type_enseigne=False).count())


def display_sources_panel(adresse: DisplayedActeur) -> bool:
    return bool(adresse.source and adresse.source.afficher)


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
            "action_list_display": action_list_display,
            "display_search": display_search,
            "display_infos_panel": display_infos_panel,
            "display_sources_panel": display_sources_panel,
            "display_labels_panel": display_labels_panel,
            "distance_to_acteur": distance_to_acteur,
            "is_embedded": is_embedded,
            "is_iframe": is_iframe,
            "is_carte": is_carte,
            "reverse": reverse,
            "static": static,
            "str_diff": str_diff,
            "quote_plus": lambda u: quote_plus(u),
            "ENVIRONMENT": settings.ENVIRONMENT,
            "AIRFLOW_WEBSERVER_REFRESHACTEUR_URL": (
                settings.AIRFLOW_WEBSERVER_REFRESHACTEUR_URL
            ),
        }
    )
    return env
