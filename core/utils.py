from django.conf import settings

from qfdmo.models import CachedDirectionAction


def get_direction(request):
    default_direction = (
        None
        if request.GET.get("carte") is not None
        else settings.DEFAULT_ACTION_DIRECTION
    )
    direction = request.GET.get("direction", default_direction)
    if direction not in [d["code"] for d in CachedDirectionAction.get_directions()]:
        direction = default_direction
    return direction
