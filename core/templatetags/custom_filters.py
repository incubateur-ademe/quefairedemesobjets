import json
import math
import random
from urllib.parse import quote_plus

from django.http import HttpRequest
from django.template.defaulttags import register
from django.urls import reverse
from django.utils.safestring import mark_safe

from core.utils import get_direction
from qfdmo.models.acteur import DisplayedActeur
from qfdmo.models.action import get_actions_by_direction


@register.filter
def options_in_json(optgroups):
    return mark_safe(
        json.dumps(
            [
                option["label"]
                for _, group_choices, _ in optgroups
                for option in group_choices
            ],
            ensure_ascii=False,
        )
    )


@register.filter
def hide_object_filter(request) -> bool:
    return bool(request.GET.get("sc_id"))


@register.filter
def random_int() -> int:
    return math.floor(random.random() * 10000)


@register.filter
def adresse_is_ok(form, acteurs) -> int:
    return bool(form.initial.adresse or form.initial.bounding_box or acteurs)


@register.filter
def json_acteur_for_display(acteur, args):
    direction, action_list, carte = args
    return acteur.json_acteur_for_display(
        direction=direction, action_list=action_list, carte=carte
    )


@register.filter
def build_args_acteur_for_display(form, carte) -> dict:
    return {
        "direction": form.initial["direction"],
        "action_list": form.initial["action_list"],
        "carte": carte,
    }


@register.filter
def distance_to_acteur(adresse: DisplayedActeur, request: HttpRequest) -> str:
    long = request.GET.get("longitude")
    lat = request.GET.get("latitude")
    point = adresse.location

    if long and lat and point and not adresse.is_digital:
        dist = (
            math.sqrt((point.y - float(lat)) ** 2 + (point.x - float(long)) ** 2)
            * 111320
        )
        return (
            f"({str(round(dist/1000,1)).replace('.',',')} km)"
            if dist >= 1000
            else f"({round(dist/10)*10} m)"
        )
    return ""


@register.filter
def get_share_url(adresse: DisplayedActeur, request: HttpRequest) -> str:
    protocol = "https" if request.is_secure() else "http"
    host = request.get_host()
    base_url = f"{protocol}://{host}"
    base_url += reverse("qfdmo:adresse_detail", args=[adresse.identifiant_unique])

    params = []
    if "carte" in request.GET:
        params.append("carte=1")
    elif "iframe" in request.GET:
        params.append("iframe=1")
    return f"{base_url}?{'&'.join(params)}"


@register.filter
def str_quote_plus(u):
    return quote_plus(u)


@register.filter
def action_by_direction(request: HttpRequest, direction: str):
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


@register.filter
def proposition_services_by_direction(adresse, direction):
    return adresse.proposition_services_by_direction(direction)
