from typing import List

from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse

from jinja2 import Environment
from qfdmo.models import Action


def is_iframe(request: HttpRequest) -> bool:
    return "iframe" in request.GET


def action_list_display(request: HttpRequest) -> List[str]:
    if action_list := request.GET.get("action_list"):
        actions = Action.objects.filter(nom__in=action_list.split("|"))
    else:
        direction = request.GET.get("direction", "jai")
        actions = Action.objects.filter(directions__nom=direction)
    return [action.nom_affiche for action in actions.order_by("order")]


def action_by_direction(request: HttpRequest, direction: str):
    action_list = request.GET.get("action_list", "").split("|")
    all_active = request.GET.get("direction") != direction or action_list == [""]

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
        }
    )
    return env
