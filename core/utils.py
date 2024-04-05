from django.conf import settings

from qfdmo.models import CachedDirectionAction


def get_direction(request):
    direction = request.GET.get("direction", settings.DEFAULT_ACTION_DIRECTION)
    if direction not in [d["code"] for d in CachedDirectionAction.get_directions()]:
        direction = settings.DEFAULT_ACTION_DIRECTION
    return direction
