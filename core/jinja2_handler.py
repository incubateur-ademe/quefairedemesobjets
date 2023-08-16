from django.http import HttpRequest
from django.templatetags.static import static
from django.urls import reverse

from jinja2 import Environment


def is_iframe(request: HttpRequest) -> bool:
    return "iframe" in request.GET


def environment(**options):
    env = Environment(**options)
    env.globals.update(
        {
            "static": static,
            "reverse": reverse,
            "is_iframe": is_iframe,
        }
    )
    return env
