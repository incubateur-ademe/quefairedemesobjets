import difflib
from typing import List

from django.conf import settings
from django.db.models import QuerySet
from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse

from jinja2 import Environment
from qfdmo.models import Action


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
def get_action_list(request: HttpRequest) -> QuerySet[Action]:
    if action_list := request.GET.get("action_list"):
        return Action.objects.filter(nom__in=action_list.split("|")).order_by("order")
    else:
        direction = request.GET.get("direction", settings.DEFAULT_ACTION_DIRECTION)
        return Action.objects.filter(directions__nom=direction).order_by("order")


def action_list_display(request: HttpRequest) -> List[str]:
    return [action.nom_affiche for action in get_action_list(request)]


def action_by_direction(request: HttpRequest, direction: str):
    action_list = [
        action for action in request.GET.get("action_list", "").split("|") if action
    ]
    all_active = request.GET.get("direction") != direction or action_list == []

    return [
        {
            **action.serialize(),
            "active": True if all_active else action.nom in action_list,
        }
        for action in Action.objects.filter(directions__nom=direction).order_by("order")
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
        }
    )
    return env
