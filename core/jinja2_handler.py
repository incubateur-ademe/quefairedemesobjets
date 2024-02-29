import difflib
from typing import List

from django.conf import settings
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse

from core.utils import get_direction
from jinja2 import Environment
from qfdmo.models import CachedDirectionAction


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


def is_iframe(request: HttpRequest) -> bool:
    return "iframe" in request.GET


# FIXME : perhaps it is better in util list ?
def get_action_list(request: HttpRequest) -> List[dict]:
    direction = get_direction(request)
    if action_list := request.GET.get("action_list"):
        return [
            a
            for a in CachedDirectionAction.get_actions_by_direction()[direction]
            if a["nom"] in action_list.split("|")
        ]
    else:
        return CachedDirectionAction.get_actions_by_direction()[direction]


def action_list_display(request: HttpRequest) -> List[str]:
    return [action["nom_affiche"] for action in get_action_list(request)]


def action_by_direction(request: HttpRequest, direction: str):
    action_list = request.GET.get("action_list")
    requested_direction = get_direction(request)
    if requested_direction != direction:
        action_list = None
    if action_list:
        return [
            {
                **a,
                "active": bool(a["nom"] in action_list),
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


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": static,
            "reverse": reverse,
            "is_iframe": is_iframe,
            "action_by_direction": action_by_direction,
            "action_list_display": action_list_display,
            "str_diff": str_diff,
            "ENVIRONMENT": settings.ENVIRONMENT,
        }
    )
    return env
