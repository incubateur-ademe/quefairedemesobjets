from django.conf import settings

from qfdmo.models.action import get_directions


def get_direction(request, is_carte=False):
    default_direction = None if is_carte else settings.DEFAULT_ACTION_DIRECTION
    direction = request.GET.get("direction", default_direction)
    if direction not in [d["code"] for d in get_directions()]:
        direction = default_direction
    return direction


def generate_google_maps_itineraire_url(latitude, longitude, displayed_acteur):
    return (
        "https://www.google.com/maps/dir/?api=1&origin="
        f"{latitude},{longitude}"
        f"&destination={displayed_acteur.latitude},"
        f"{displayed_acteur.longitude}&travelMode=WALKING"
    )
